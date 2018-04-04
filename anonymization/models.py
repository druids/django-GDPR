from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class LegalPurpose:
    CHOICES = (
        ('legal-purpose-1', 'Legal purpose 1'),
        ('legal-purpose-2', 'Legal purpose 2'),
    )


class LegalReason(models.Model):
    created_at = models.DateTimeField(verbose_name='created at', null=False, blank=False, auto_now_add=True,
                                      db_index=True)
    changed_at = models.DateTimeField(verbose_name='changed at', null=False, blank=False, auto_now=True, db_index=True)
    expires_at = models.DateTimeField(verbose_name='expires at', null=False, blank=False, db_index=True)
    tag = models.CharField(verbose_name='tag', null=True, blank=True, max_length=100)
    is_active = models.BooleanField(verbose_name='is active', null=False, blank=False, default=True)


class LegalReasonRelatedObject(models.Model):
    purpose_slug = models.CharField(LegalPurpose, verbose_name='purpose', null=False, blank=False,
                                    choices=LegalPurpose.CHOICES)
    legal_reason = models.ForeignKey(LegalReason, verbose_name='legal reason', null=False, blank=False,
                                     related_name='related_objects')
    content_type = models.ForeignKey(ContentType, verbose_name='content type of the related object', null=False,
                                     blank=False)
    object_id = models.TextField(verbose_name='ID of the related object', null=False, blank=False)
    content_object = GenericForeignKey('content_type', 'object_id')


class AnonymizedData(models.Model):
    anonymized_object = models.ForeignKey(LegalReasonRelatedObject, verbose_name='anonymized object', null=False,
                                          blank=False, related_name='anonymized_data')
    field = models.TextField(verbose_name='anonymized field', null=False, blank=False)
    type = models.TextField(verbose_name='type', null=True, blank=True)
    is_active = models.BooleanField(verbose_name='is active', null=False, blank=False, default=True)
    expired_reason = models.ForeignKey(LegalReason, verbose_name='expired reason', null=True, blank=True)
