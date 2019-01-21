from typing import Any, Dict, ItemsView, Iterator, KeysView, List, Optional, TYPE_CHECKING, Tuple, Union, ValuesView

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Model, QuerySet

from gdpr.anonymizers.base import FieldAnonymizer, ModelAnonymizerMeta
from gdpr.loading import anonymizer_register
from gdpr.models import AnonymizedData, LegalReason

if TYPE_CHECKING:
    from gdpr.purposes.default import AbstractPurpose

FieldList = Union[List, Tuple, KeysView[str]]  # List, tuple or return of dict keys() method.
FieldMatrix = Union[str, Tuple[Any, ...]]


class ModelAnonymizerBase(metaclass=ModelAnonymizerMeta):
    can_anonymize_qs: bool
    fields: Dict[str, FieldAnonymizer]

    @property
    def model(self) -> Model:
        return self.Meta.model  # type: ignore

    @property
    def content_type(self) -> ContentType:
        """Get model ContentType"""
        return ContentType.objects.get_for_model(self.model)

    def __getitem__(self, item: str) -> FieldAnonymizer:
        return self.fields[item]

    def __contains__(self, item: str) -> bool:
        return item in self.fields.keys()

    def __iter__(self) -> Iterator[str]:
        for i in self.fields:
            yield i

    def keys(self) -> KeysView[str]:
        return self.fields.keys()

    def items(self) -> ItemsView[str, FieldAnonymizer]:
        return self.fields.items()

    def values(self) -> ValuesView[FieldAnonymizer]:
        return self.fields.values()

    def get(self, *args, **kwargs) -> Union[FieldAnonymizer, Any]:
        return self.fields.get(*args, **kwargs)

    def is_field_anonymized(self, obj: Model, name: str) -> bool:
        """Check if field have AnonymizedData record"""
        return AnonymizedData.objects.filter(
            field=name, is_active=True, content_type=self.content_type, object_id=str(obj.pk)
        ).exists()

    def mark_field_as_anonymized(self, obj: Model, name: str, legal_reason: Optional[LegalReason] = None) -> None:
        AnonymizedData(object=obj, field=name, expired_reason=legal_reason).save()

    def get_anonymized_value_from_obj(self, field: FieldAnonymizer, obj: Model, name: str) -> Any:
        """Get from field, obj and field name anonymized value."""
        return field.get_anonymized_value_from_obj(obj, name)

    def get_local_fields(self, fields: FieldMatrix) -> FieldList:
        """Get Iterable of local fields from fields matrix."""
        for i in fields:
            if type(i) not in [str, list, tuple]:
                raise ImproperlyConfigured()
        if fields == "__ALL__":
            return self.fields.keys()
        local_fields = [i for i in fields if type(i) == str]
        if "__ALL__" in local_fields:
            return self.fields.keys()
        return local_fields

    def get_related_fields(self, fields: FieldMatrix) -> Dict[str, Any]:
        """Get Dictionary of related fields from fields matrix."""
        related_fields = [i for i in fields if type(i) in [list, tuple]]
        for i in related_fields:
            if len(i) != 2:
                raise ImproperlyConfigured()
        return {i[0]: i[1] for i in related_fields}

    def parse_fields_matrix(self, fields: FieldMatrix) -> Tuple[FieldList, Dict[str, Any]]:
        """Parse fields matrix into local fields and related fields"""
        if type(fields) not in [str, tuple, list]:
            raise ImproperlyConfigured()
        return self.get_local_fields(fields), self.get_related_fields(fields)

    def perform_anonymization(self, obj: Model, updated_data: dict,
                              legal_reason: Optional[LegalReason] = None) -> None:
        """Update data in database and mark them as anonymized."""
        with transaction.atomic():
            obj.__class__.objects.filter(pk=obj.pk).update(**updated_data)
            for i in updated_data.keys():
                self.mark_field_as_anonymized(obj, i, legal_reason)

    def anonymize_qs(self, qs: QuerySet) -> None:
        raise NotImplementedError()

    def anonymize_obj(self, obj: Model, legal_reason: Optional[LegalReason] = None,
                      purpose: Optional["AbstractPurpose"] = None,
                      fields: FieldMatrix = "__ALL__"):
        local_fields, related_fields = self.parse_fields_matrix(fields)

        # Filter out already anonymized fields
        local_fields_non_anonymized = [i for i in local_fields if not self.is_field_anonymized(obj, i)]
        update_dict = {name: self.get_anonymized_value_from_obj(self[name], obj, name) for name in
                       local_fields_non_anonymized}

        self.perform_anonymization(obj, update_dict, legal_reason)

        for key in related_fields.keys():
            related_attribute = getattr(obj, key)
            o_anonymizer = None
            for o in related_attribute.all():
                if not o_anonymizer:
                    o_anonymizer = anonymizer_register[o.__class__]
                o_anonymizer().anonymize_obj(o, legal_reason, purpose=purpose, fields=related_fields[key])


class ModelAnonymizer(ModelAnonymizerBase):
    """
    Default model anonymizer that supports anonymization per object.
    Child must define Meta class with model (like factoryboy)
    """

    can_anonymize_qs = False
    chunk_size = 10000


class DeleteModelAnonymizer(ModelAnonymizer):
    """
    The simpliest anonymization class that is used for removing whole input queryset.
    """

    can_anonymize_qs = True

    def anonymize_obj(self, obj: Model, legal_reason: Optional["LegalReason"] = None,
                      purpose: Optional["AbstractPurpose"] = None,
                      fields: Optional[FieldMatrix] = "__ALL__"):
        obj.__class__.objects.filter(pk=obj.pk).delete()

    def anonymize_qs(self, qs):
        qs.delete()
