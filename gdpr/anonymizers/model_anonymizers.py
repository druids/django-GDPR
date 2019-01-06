from gdpr.anonymizers.base import ModelAnonymizerBase


class ModelAnonymizer(metaclass=ModelAnonymizerBase):
    """
    Default model anonymizer that supports anonymization per object.
    Child must define Meta class with model (like factoryboy)
    """

    can_anonymize_qs = False
    chunk_size = 10000

    def anonymize_obj(self, obj):
        updated_data = {name: field.get_anonymized_value_from_obj(obj, name) for name, field in self.fields.items()}
        obj.__class__.objects.filter(pk=obj.pk).update(**updated_data)


class DeleteModelAnonymizer(ModelAnonymizer):
    """
    The simpliest anonymization class that is used for removing whole input queryset.
    """

    can_anonymize_qs = True

    def anonymize_obj(self, obj):
        obj.__class__.objects.filter(pk=obj.pk).delete()

    def anonymize_qs(self, qs):
        qs.delete()
