from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.db.utils import Error

from gdpr.models import AnonymizedData, LegalReasonRelatedObject


class AnonymizationModelMixin:
    @property
    def content_type(self) -> ContentType:
        """Get model ContentType"""
        return ContentType.objects.get_for_model(self.__class__)

    def anonymize_obj(self, *args, **kwargs):
        from gdpr.loading import anonymizer_register
        if self.__class__ in anonymizer_register:
            anonymizer_register[self.__class__]().anonymize_obj(self, *args, **kwargs)
        else:
            raise ImproperlyConfigured("%s does not have registered anonymizer." % self.__class__)

    def delete(self, using=None, keep_parents=False):
        """Cleanup anonymization metadata"""
        obj_id = str(self.pk)
        super().delete(using, keep_parents)
        try:
            AnonymizedData.objects.filter(object_id=obj_id, content_type=self.content_type).delete()
        except Error:
            pass  # Better to just have some leftovers then to fail
        try:
            LegalReasonRelatedObject.objects.filter(object_id=obj_id, content_type=self.content_type).delete()
        except Error:
            pass  # Better to just have some leftovers then to fail


class AnonymizationModel(AnonymizationModelMixin, Model):
    class Meta:
        abstract = True
