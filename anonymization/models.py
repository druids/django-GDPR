import reversion
from chamber.models import SmartModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import string_concat
from django.db import models
from anonymization.purposes.default import purposes_map


@reversion.register
class LegalReason(SmartModel):
    created_at = models.DateTimeField(verbose_name='created at', null=False, blank=False, auto_now_add=True,
                                      db_index=True)
    changed_at = models.DateTimeField(verbose_name='changed at', null=False, blank=False, auto_now=True, db_index=True)
    expires_at = models.DateTimeField(verbose_name='expires at', null=False, blank=False, db_index=True)
    tag = models.CharField(verbose_name='tag', null=True, blank=True, max_length=100)
    is_active = models.BooleanField(verbose_name='is active', null=False, blank=False, default=True)
    purpose_slug = models.CharField(verbose_name='purpose', null=False, blank=False,
                                    choices=((purpose_slug,
                                              string_concat(purpose_slug, ' - ', purpose_class.name))
                                             for purpose_slug, purpose_class in purposes_map.items()))
    source_object_content_type = models.ForeignKey(ContentType,
                                                   verbose_name='source ocontent type of the related object',
                                                   null=False, blank=False)
    source_object_id = models.TextField(verbose_name='source object ID', null=False, blank=False)
    source = GenericForeignKey('source_object_content_type', 'source_object_id')


class LegalReasonRelatedObject(SmartModel):
    legal_reason = models.ForeignKey(LegalReason, verbose_name='legal reason', null=False, blank=False,
                                     related_name='related_objects')
    content_type = models.ForeignKey(ContentType, verbose_name='related object content type', null=False,
                                     blank=False)
    object_id = models.TextField(verbose_name='related object ID', null=False, blank=False)
    content_object = GenericForeignKey('content_type', 'object_id')


class AnonymizedData(SmartModel):
    field = models.CharField(verbose_name='anonymized field', max_length=250, null=False, blank=False)
    content_type = models.ForeignKey(ContentType, verbose_name='related object content type', null=False,
                                     blank=False)
    object_id = models.TextField(verbose_name='related object ID', null=False, blank=False)
    related_object = GenericForeignKey('content_type', 'object_id')
    is_active = models.BooleanField(verbose_name='is active', null=False, blank=False, default=True)
    expired_reason = models.ForeignKey(LegalReason, verbose_name='expired reason', null=True, blank=True)
