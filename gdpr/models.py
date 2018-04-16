from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db import models

from chamber.models import SmartModel

from .purposes.default import purposes_map


class LegalReason(SmartModel):

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

    class Meta:
        verbose_name = _('anonymized data')
        verbose_name_plural = _('anonymized data')
        ordering = ('-created_at',)
