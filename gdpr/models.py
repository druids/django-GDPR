from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from chamber.models import SmartModel

from typing import TYPE_CHECKING, Iterable, Optional, Type

from enumfields import NumEnumField

from .enums import LegalReasonState
from .loading import purpose_register


if TYPE_CHECKING:
    from gdpr.purposes.default import AbstractPurpose


class LegalReasonManager(models.Manager):

    def create_consent(self, purpose_slug: str, source_object, issued_at: Optional[datetime] = None,
                       tag: Optional[str] = None, related_objects: Optional[Iterable[Type[models.Model]]] = None):
        """
        Create (or update, if it exist) a LegalReason with purpose slug for concrete object instance

        Args:
            purpose_slug: String of Legal Reason purpose
            source_object: Source object this Legal Reason is related to
            issued_at: When the Legal Reason consent was given
            tag: String that the developer can add to the created consent and use it to mark his business processes
            related_objects: Objects this Legal Reason relates to (ie. order, registrations etc.)

        Returns:
            Legal Reason: LegalReason object
        """
        try:
            purpose = purpose_register[purpose_slug]
        except KeyError:
            raise KeyError('Purpose with slug {} does not exits'.format(purpose_slug))
        issued_at = issued_at or timezone.now()

        legal_reason, created = LegalReason.objects.get_or_create(
            source_object_content_type=ContentType.objects.get_for_model(source_object.__class__),
            source_object_id=str(source_object.pk),
            purpose_slug=purpose_slug,
            defaults={
                'issued_at': issued_at,
                'expires_at': issued_at + purpose.expiration_timedelta,
                'tag': tag,
                'state': LegalReasonState.ACTIVE,
            }
        )

        if not created:
            legal_reason.change_and_save(
                expires_at=timezone.now() + purpose.expiration_timedelta,
                tag=tag,
                state=LegalReasonState.ACTIVE
            )

        for related_object in related_objects or ():
            legal_reason.related_objects.update_or_create(
                object_content_type=ContentType.objects.get_for_model(related_object.__class__),
                object_id=related_object.pk
            )

        return legal_reason

    def deactivate_consent(self, purpose_slug: str, source_object):
        """
        Deactivate/Remove consent (Legal reason) for source_object, purpose_slug combination

        Args:
            purpose_slug: Purpose slug to deactivate consent for
            source_object: Source object to deactivate consent for

        Returns:
            List of LegalReason objects
        """
        reasons = []
        for reason in LegalReason.objects.filter_source_instance_active_non_expired_purpose(source_object,
                                                                                            purpose_slug):
            reason.deactivate()
            reasons.append(reason)
        return reasons

    def exists_valid_consent(self, purpose_slug: str, source_object):
        """
        Returns True if source_object has valid (ie. active and non-expired) consent (Legal Reason)

        Args:
            purpose_slug: Purpose_slug to check consent for
            source_object: Source object to check consent for
        """
        return LegalReason.objects.filter_source_instance_active_non_expired_purpose(
            source_object, purpose_slug).exists()

    def exists_deactivated_consent(self, purpose_slug: str, source_object):
        """
        Returns True if source_object has deactivated consent (Legal Reason)

        Args:
            purpose_slug: Purpose_slug to check consent for
            source_object: Source object to check consent for
        """
        return self.filter_source_instance(source_object).filter(
            state=LegalReasonState.DEACTIVATED,
            purpose_slug=purpose_slug
        ).exists()

    def expire_old_consents(self):
        """
        Anonymize and expire consents which have past their `expires_at`.
        """
        for reason in LegalReason.objects.filter_active_and_expired():
            reason.expire()


class LegalReasonQuerySet(models.QuerySet):

    def filter_expired_retaining_data_in_last_days(self, days=None):
        """
        Filters all Legal Reason that retain data and that expired in last days

        Args:
            days: Number of days in the past. If not provided, all Legal Reasons retaining data which expired in the
            past will be returned.
        """
        purpose_slugs_retaining_data = [slug for slug, cls in purpose_register.items() if cls.fields]

        filter_keys = {
            'expires_at__lt': timezone.now(),
        } if days is None else {
            'expires_at__gt': timezone.now() - relativedelta(days=days),
            'expires_at__lt': timezone.now()
        }

        return self.filter(state=LegalReasonState.ACTIVE, purpose_slug__in=purpose_slugs_retaining_data, **filter_keys)

    def filter_non_expired(self):
        return self.filter(Q(expires_at__gte=timezone.now()) | Q(expires_at=None))

    def filter_expired(self):
        return self.filter(expires_at__lte=timezone.now())

    def filter_active(self):
        return self.filter(state=LegalReasonState.ACTIVE)

    def filter_active_and_non_expired(self):
        return self.filter_active().filter_non_expired()

    def filter_active_and_expired(self):
        return self.filter_active().filter_expired()

    def filter_source_instance(self, source_object):
        return self.filter(
            source_object_content_type=ContentType.objects.get_for_model(source_object.__class__),
            source_object_id=str(source_object.pk)
        )

    def filter_source_instance_active_non_expired(self, source_object):
        return self.filter_source_instance(source_object).filter_active_and_non_expired()

    def filter_source_instance_active_non_expired_purpose(self, source_object, purpose_slug: str):
        return self.filter_source_instance_active_non_expired(source_object).filter(
            purpose_slug=purpose_slug
        )


class LegalReason(SmartModel):
    objects = LegalReasonManager.from_queryset(LegalReasonQuerySet)()

    issued_at = models.DateTimeField(
        verbose_name=_('issued at'),
        null=False,
        blank=False,
    )
    expires_at = models.DateTimeField(
        verbose_name=_('expires at'),
        null=True,
        blank=True,
        db_index=True
    )
    tag = models.CharField(
        verbose_name=_('tag'),
        null=True,
        blank=True,
        max_length=100
    )
    state = NumEnumField(
        verbose_name=_('state'),
        null=False,
        blank=False,
        enum=LegalReasonState,
        default=LegalReasonState.ACTIVE,
        db_index=True
    )
    purpose_slug = models.CharField(
        verbose_name=_('purpose'),
        null=False,
        blank=False,
        max_length=100,
        db_index=True
    )
    source_object_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('source object content type'),
        null=False,
        blank=False,
        on_delete=models.DO_NOTHING
    )
    source_object_id = models.TextField(
        verbose_name=_('source object ID'),
        null=False, blank=False,
        db_index=True
    )
    source_object = GenericForeignKey(
        'source_object_content_type', 'source_object_id'
    )

    class Meta:
        verbose_name = _('legal reason')
        verbose_name_plural = _('legal reasons')
        ordering = ('-created_at',)
        unique_together = ('purpose_slug', 'source_object_content_type', 'source_object_id')

    def __str__(self):
        return f'{self.purpose.name}'

    @property
    def is_active(self):
        return self.state == LegalReasonState.ACTIVE

    @property
    def purpose(self) -> Type["AbstractPurpose"]:
        return purpose_register.get(self.purpose_slug, None)

    def _anonymize_obj(self, *args, **kwargs):
        purpose_register[self.purpose_slug]().anonymize_obj(self.source_object, self, *args, **kwargs)

    def _deanonymize_obj(self, *args, **kwargs):
        purpose_register[self.purpose_slug]().deanonymize_obj(self.source_object, *args, **kwargs)

    def expire(self):
        """Anonymize obj and set state as expired."""
        with transaction.atomic():
            self._anonymize_obj()
            self.change_and_save(state=LegalReasonState.EXPIRED)

    def deactivate(self):
        """Deactivate obj and run anonymization."""
        with transaction.atomic():
            self._anonymize_obj()
            self.change_and_save(state=LegalReasonState.DEACTIVATED)

    def renew(self):
        with transaction.atomic():
            self.change_and_save(
                expires_at=timezone.now() + purpose_register[self.purpose_slug]().expiration_timedelta,
                state=LegalReasonState.ACTIVE
            )
            self._deanonymize_obj()


class LegalReasonRelatedObject(SmartModel):
    legal_reason = models.ForeignKey(
        LegalReason,
        verbose_name=_('legal reason'),
        null=False,
        blank=False,
        related_name='related_objects',
        on_delete=models.CASCADE
    )
    object_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('related object content type'),
        null=False,
        blank=False,
        on_delete=models.DO_NOTHING
    )
    object_id = models.TextField(
        verbose_name=_('related object ID'),
        null=False,
        blank=False,
        db_index=True
    )
    object = GenericForeignKey(
        'object_content_type', 'object_id'
    )

    class Meta:
        verbose_name = _('legal reason related object')
        verbose_name_plural = _('legal reasons related objects')
        ordering = ('-created_at',)
        unique_together = ('legal_reason', 'object_content_type', 'object_id')

    def __str__(self):
        return '{legal_reason} {object}'.format(legal_reason=self.legal_reason, object=self.object)


class AnonymizedDataQuerySet(models.QuerySet):

    def filter_source_instance_active(self, source_object):
        return self.filter(
            content_type=ContentType.objects.get_for_model(source_object.__class__),
            object_id=str(source_object.pk),
            is_active=True
        )


class AnonymizedData(SmartModel):
    objects = models.Manager.from_queryset(AnonymizedDataQuerySet)()

    field = models.CharField(
        verbose_name=_('anonymized field name'),
        max_length=250,
        null=False,
        blank=False
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('related object content type'),
        null=False,
        blank=False,
        on_delete=models.DO_NOTHING
    )
    object_id = models.TextField(
        verbose_name=_('related object ID'),
        null=False,
        blank=False
    )
    object = GenericForeignKey(
        'content_type', 'object_id'
    )
    is_active = models.BooleanField(
        verbose_name=_('is active'),
        default=True
    )
    expired_reason = models.ForeignKey(
        LegalReason,
        verbose_name=_('expired reason'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _('anonymized data')
        verbose_name_plural = _('anonymized data')
        ordering = ('-created_at',)
        unique_together = ('content_type', 'object_id', 'field')

    def __str__(self):
        return '{field} {object}'.format(field=self.field, object=self.object)
