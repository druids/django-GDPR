import warnings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, QuerySet
from django.db.utils import Error

from gdpr.models import AnonymizedData, LegalReason, LegalReasonRelatedObject


class AnonymizationModelMixin:

    @property
    def content_type(self) -> ContentType:
        """Get model ContentType"""
        return ContentType.objects.get_for_model(self.__class__)

    def _anonymize_obj(self, *args, **kwargs):
        from gdpr.loading import anonymizer_register
        if self.__class__ in anonymizer_register:
            anonymizer_register[self.__class__]().anonymize_obj(self, *args, **kwargs)
        else:
            raise ImproperlyConfigured('%s does not have registered anonymizer.' % self.__class__)

    def _deanonymize_obj(self, *args, **kwargs):
        from gdpr.loading import anonymizer_register
        if self.__class__ in anonymizer_register:
            anonymizer_register[self.__class__]().deanonymize_obj(self, *args, **kwargs)
        else:
            raise ImproperlyConfigured('%s does not have registered anonymizer.' % self.__class__)

    def get_consents(self) -> QuerySet:
        return LegalReason.objects.filter_source_instance(self)

    def create_consent(self, purpose_slug: str, *args, **kwargs) -> LegalReason:
        return LegalReason.objects.create_consent(purpose_slug, self, *args, **kwargs)

    def deactivate_consent(self, purpose_slug: str):
        LegalReason.objects.deactivate_consent(purpose_slug, self)

    def delete(self, *args, **kwargs):
        """Cleanup anonymization metadata"""
        obj_id = str(self.pk)
        super().delete(*args, **kwargs)
        try:
            AnonymizedData.objects.filter(object_id=obj_id, content_type=self.content_type).delete()
        except Error as e:
            # Better to just have some leftovers then to fail
            warnings.warn(f'An exception {str(e)} occurred during cleanup of {str(self)}')
        try:
            LegalReasonRelatedObject.objects.filter(object_id=obj_id, object_content_type=self.content_type).delete()
        except Error as e:
            # Better to just have some leftovers then to fail
            warnings.warn(f'An exception {str(e)} occurred during cleanup of {str(self)}')


class AnonymizationModel(AnonymizationModelMixin, Model):
    class Meta:
        abstract = True
