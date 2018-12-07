from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from chamber.models import SmartModel

from .purposes.default import purposes_map


class LegalReasonManager(models.Manager):

    def create_from_purpose_slug(self, purpose_slug, source_object, issued_at=None, tag=None, related_objects=None):
        try:
            purpose = purposes_map[purpose_slug]
            issued_at = issued_at or timezone.now()

            legal_reason = LegalReason.objects.create(
                issued_at=issued_at,
                expires_at=issued_at + purpose.expiration_timedelta,
                tag=tag,
                purpose_slug=purpose_slug,
                source_object=source_object
            )
            for related_object in related_objects or ():
                legal_reason.related_objects.create(object=related_object)
            return legal_reason
        except KeyError:
            raise KeyError('Purpose with slug {} does not exits'.format(purpose_slug))

    def exists_valid_consent(self, purpose_slug, source_object):
        return LegalReason.objects.filter(
            source_object_content_type=ContentType.objects.get_for_model(source_object.__class__),
            source_object_id=str(source_object.pk),
            purpose_slug=purpose_slug,
            is_active=True,
            expires_at__gte=timezone.now(),
        ).exists()


class LegalReason(SmartModel):

    objects = LegalReasonManager()

    issued_at = models.DateTimeField(
        verbose_name=_('issued at'),
        null=False,
        blank=False,
    )
    expires_at = models.DateTimeField(
        verbose_name=_('expires at'),
        null=False,
        blank=False,
        db_index=True
    )
    tag = models.CharField(
        verbose_name=_('tag'),
        null=True,
        blank=True,
        max_length=100
    )
    is_active = models.BooleanField(
        verbose_name=_('is active'),
        default=True
    )
    purpose_slug = models.CharField(
        verbose_name=_('purpose'),
        null=False,
        blank=False,
        choices=(
            (purpose_slug, purpose_class.name)
            for purpose_slug, purpose_class in purposes_map.items()
        ),
        max_length=100
    )
    source_object_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('source object content type'),
        null=False,
        blank=False
    )
    source_object_id = models.TextField(
        verbose_name=_('source object ID'),
        null=False, blank=False
    )
    source_object = GenericForeignKey(
        'source_object_content_type', 'source_object_id'
    )

    @property
    def purpose(self):
        return purposes_map.get(self.purpose_slug, None)

    def __str__(self):
        return '{purpose_slug}'.format(purpose_slug=self.get_purpose_slug_display())

    class Meta:
        verbose_name = _('legal reason')
        verbose_name_plural = _('legal reasons')
        ordering = ('-created_at',)


class LegalReasonRelatedObject(SmartModel):

    legal_reason = models.ForeignKey(
        LegalReason,
        verbose_name=_('legal reason'),
        null=False,
        blank=False,
        related_name='related_objects'
    )
    object_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('related object content type'),
        null=False,
        blank=False
    )
    object_id = models.TextField(
        verbose_name=_('related object ID'),
        null=False,
        blank=False
    )
    object = GenericForeignKey(
        'object_content_type', 'object_id'
    )

    def __str__(self):
        return '{legal_reason} {object}'.format(legal_reason=self.legal_reason, object=self.object)

    class Meta:
        verbose_name = _('legal reason related object')
        verbose_name_plural = _('legal reasons related objects')
        ordering = ('-created_at',)


class AnonymizedData(SmartModel):

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
        blank=False
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
        blank=True
    )

    def __str__(self):
        return '{field} {object}'.format(field=self.field, object=self.object)

    class Meta:
        verbose_name = _('anonymized data')
        verbose_name_plural = _('anonymized data')
        ordering = ('-created_at',)
