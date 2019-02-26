import hashlib
import random
import string
import warnings
from typing import (
    TYPE_CHECKING, Any, Dict, ItemsView, Iterator, KeysView, List, Optional, Tuple, Type, Union, ValuesView
)

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db import transaction
from django.db.models import Model, QuerySet
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor, ReverseManyToOneDescriptor

from gdpr.anonymizers.base import FieldAnonymizer, RelationAnonymizer
from gdpr.fields import Fields
from gdpr.models import AnonymizedData, LegalReason

if TYPE_CHECKING:
    from gdpr.purposes.default import AbstractPurpose

FieldList = Union[List, Tuple, KeysView[str]]  # List, tuple or return of dict keys() method.
FieldMatrix = Union[str, Tuple[Any, ...]]


class ModelAnonymizerMeta(type):
    """
    Metaclass for anonymizers. The main purpose of the metaclass is to register anonymizers and find field anonymizers
    defined in the class as attributes and store it to the fields property.
    """

    def __new__(cls, name, bases, attrs):
        from gdpr.loading import anonymizer_register

        new_obj = super().__new__(cls, name, bases, attrs)

        # Also ensure initialization is only performed for subclasses of ModelAnonymizer
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelAnonymizerMeta)]
        if not parents or not hasattr(new_obj, 'Meta') or getattr(new_obj.Meta, 'abstract', False):
            return new_obj

        fields = {}
        for name, obj in attrs.items():
            if isinstance(obj, FieldAnonymizer):
                fields[name] = obj
        new_obj.fields = fields
        anonymizer_register.register(new_obj.Meta.model, new_obj)
        return new_obj


class ModelAnonymizerBase(metaclass=ModelAnonymizerMeta):
    can_anonymize_qs: bool
    fields: Dict[str, FieldAnonymizer]
    _base_encryption_key = None

    class IrreversibleAnonymizerException(Exception):
        pass

    def __init__(self, base_encryption_key: Optional[str] = None):
        self._base_encryption_key = base_encryption_key

    @property
    def model(self) -> Type[Model]:
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

    def _get_encryption_key(self, obj, field_name: str):
        """Hash encryption key from `get_encryption_key` and append settings.SECRET_KEY."""
        return hashlib.sha256(
            f'{obj.pk}::{self.get_encryption_key(obj)}::{settings.SECRET_KEY}::{field_name}'.encode(
                'utf-8')).hexdigest()

    def is_reversible(self, obj) -> bool:
        if hasattr(self.Meta, 'reversible_anonymization'):  # type: ignore
            return self.Meta.reversible_anonymization  # type: ignore
        return True

    def anonymize_reversion(self, obj) -> bool:
        if hasattr(self.Meta, 'anonymize_reversion'):  # type: ignore
            return self.Meta.anonymize_reversion  # type: ignore
        return False

    def get_encryption_key(self, obj) -> str:
        if not self.is_reversible(obj):
            return ''.join(random.choices(string.digits + string.ascii_letters, k=128))
        if self._base_encryption_key:
            return self._base_encryption_key
        raise NotImplementedError(
            f'The anonymizer \'{self.__class__.__name__}\' does not have `get_encryption_key` method defined or '
            '`base_encryption_key` supplied during anonymization or '
            'reversible_anonymization set to False.')

    def set_base_encryption_key(self, base_encryption_key: str):
        self._base_encryption_key = base_encryption_key

    def is_field_anonymized(self, obj: Model, name: str) -> bool:
        """Check if field have AnonymizedData record"""
        return AnonymizedData.objects.filter(
            field=name, is_active=True, content_type=self.content_type, object_id=str(obj.pk)
        ).exists()

    @staticmethod
    def is_forward_relation(field) -> bool:
        return isinstance(field, ForwardManyToOneDescriptor)

    @staticmethod
    def is_reverse_relation(field) -> bool:
        return isinstance(field, ReverseManyToOneDescriptor)

    @staticmethod
    def is_generic_relation(field) -> bool:
        return isinstance(field, RelationAnonymizer)

    def get_related_model(self, field_name: str) -> Type[Model]:
        field = getattr(self.model, field_name, None)
        if field is None:
            if self.is_generic_relation(getattr(self, field_name, None)):
                return getattr(self, field_name).get_related_model()
            raise RuntimeError(f'Field \'{field_name}\' is not defined on {str(self.model)}')
        elif self.is_reverse_relation(field):
            return field.rel.related_model
        elif self.is_forward_relation(field):
            return field.field.related_model
        else:
            raise NotImplementedError(f'Relation {str(field)} not supported yet.')

    def mark_field_as_anonymized(self, obj: Model, name: str, legal_reason: Optional[LegalReason] = None):
        AnonymizedData.objects.create(object=obj, field=name, expired_reason=legal_reason)

    def unmark_field_as_anonymized(self, obj: Model, name: str):
        AnonymizedData.objects.filter(
            field=name, is_active=True, content_type=self.content_type, object_id=str(obj.pk)).delete()

    def get_anonymized_value_from_obj(self, field: FieldAnonymizer, obj: Model, name: str) -> Any:
        """Get from field, obj and field name anonymized value."""
        return field.get_anonymized_value_from_obj(obj, name, self._get_encryption_key(obj, name))

    def get_deanonymized_value_from_obj(self, field: FieldAnonymizer, obj: Model, name: str) -> Any:
        """Get from field, obj and field name deanonymized value."""
        return field.get_deanonymized_value_from_obj(obj, name, self._get_encryption_key(obj, name))

    def get_anonymized_value_from_version(self, field: FieldAnonymizer, obj: Model, version, name: str) -> Any:
        """Get from field, obj and field name anonymized value."""
        return field.get_anonymized_value_from_version(obj, version, name, self._get_encryption_key(obj, name))

    def get_deanonymized_value_from_version(self, field: FieldAnonymizer, obj: Model, version, name: str) -> Any:
        """Get from field, obj and field name deanonymized value."""
        return field.get_deanonymized_value_from_version(obj, version, name, self._get_encryption_key(obj, name))

    def _perform_anonymization(self, obj: Model, updated_data: dict,
                               legal_reason: Optional[LegalReason] = None):
        obj.__class__.objects.filter(pk=obj.pk).update(**updated_data)
        for i in updated_data.keys():
            self.mark_field_as_anonymized(obj, i, legal_reason)

    def _perform_deanonymization(self, obj: Model, updated_data: dict):
        obj.__class__.objects.filter(pk=obj.pk).update(**updated_data)
        for i in updated_data.keys():
            self.unmark_field_as_anonymized(obj, i)

    def perform_anonymization(self, obj: Model, updated_data: dict,
                              legal_reason: Optional[LegalReason] = None):
        """Update data in database and mark them as anonymized."""
        with transaction.atomic():
            self._perform_anonymization(obj, updated_data, legal_reason)

    def perform_deanonymization(self, obj: Model, updated_data: dict):
        """Update data in database and mark them as anonymized."""
        with transaction.atomic():
            self._perform_deanonymization(obj, updated_data)

    @staticmethod
    def _perform_version_update(model: Type[Model], version, update_data):
        from reversion import revisions
        version_dict_local = dict(version.field_dict)
        version_dict_local.update(update_data)
        local_obj = model(**version_dict_local)
        if hasattr(revisions, '_get_options'):
            version_options = revisions._get_options(model)
            version_format = version_options.format
            version_fields = version_options.fields
        else:
            version_adapter = revisions.get_adapter(model)
            version_format = version_adapter.get_serialization_format()
            version_fields = list(version_adapter.get_fields_to_serialize())
        version.serialized_data = serializers.serialize(
            version_format,
            (local_obj,),
            fields=version_fields
        )
        version.save()

    def perform_anonymization_with_version(self, obj: Model, updated_data: Dict[str, Any],
                                           updated_version_data: List[Tuple[Any, Dict]],
                                           legal_reason: Optional[LegalReason] = None):
        """Update data in database and versions and mark them as anonymized."""
        with transaction.atomic():
            # first we need to update versions
            for version, version_dict in updated_version_data:
                self._perform_version_update(obj.__class__, version, version_dict)
            self._perform_anonymization(obj, updated_data, legal_reason)

    def perform_deanonymization_with_version(self, obj: Model, updated_data: Dict,
                                             updated_version_data: List[Tuple[Any, Dict]]):
        """Update data in database and mark them as anonymized."""
        with transaction.atomic():
            # first we need to update versions
            for version, version_dict in updated_version_data:
                self._perform_version_update(obj.__class__, version, version_dict)
            self._perform_deanonymization(obj, updated_data)

    def anonymize_qs(self, qs: QuerySet) -> None:
        raise NotImplementedError()

    def deanonymize_qs(self, qs: QuerySet) -> None:
        raise NotImplementedError()

    def anonymize_obj(self, obj: Model, legal_reason: Optional[LegalReason] = None,
                      purpose: Optional["AbstractPurpose"] = None,
                      fields: Union[Fields, FieldMatrix] = '__ALL__', base_encryption_key: Optional[str] = None):

        if base_encryption_key:
            self.set_base_encryption_key(base_encryption_key)

        parsed_fields: Fields = Fields(fields, obj.__class__) if not isinstance(fields, Fields) else fields

        # Filter out already anonymized fields
        raw_local_fields = [i for i in parsed_fields.local_fields if not self.is_field_anonymized(obj, i)]
        update_dict = {name: self.get_anonymized_value_from_obj(self[name], obj, name) for name in raw_local_fields}

        if self.anonymize_reversion(obj):
            from reversion.models import Version
            from gdpr.utils import get_reversion_versions, get_reversion_local_field_dict
            versions: List[Version] = get_reversion_versions(obj)
            versions_update_dict = [
                (
                    version,
                    {
                        name: self.get_anonymized_value_from_version(self[name], obj, version, name)
                        for name in raw_local_fields
                        if name in get_reversion_local_field_dict(version)
                    }
                )
                for version in versions
            ]
            self.perform_anonymization_with_version(obj, update_dict, versions_update_dict, legal_reason)
        else:
            self.perform_anonymization(obj, update_dict, legal_reason)

        for name, related_fields in parsed_fields.related_fields.items():
            related_attribute = getattr(obj, name, None)
            related_metafield = getattr(obj.__class__, name, None)
            if self.is_reverse_relation(related_metafield):
                for related_obj in related_attribute.all():
                    related_fields.anonymizer.anonymize_obj(
                        related_obj, legal_reason, purpose, related_fields,
                        base_encryption_key=self._get_encryption_key(obj, name))
            elif self.is_forward_relation(related_metafield) and related_attribute is not None:
                related_fields.anonymizer.anonymize_obj(
                    related_attribute, legal_reason, purpose, related_fields,
                    base_encryption_key=self._get_encryption_key(obj, name))
            elif related_attribute is None and related_metafield is None:
                if self.is_generic_relation(getattr(self, name, None)):
                    objs = getattr(self, name).get_related_objects(obj)
                    for related_obj in objs:
                        related_fields.anonymizer.anonymize_obj(
                            related_obj, legal_reason, purpose, related_fields,
                            base_encryption_key=self._get_encryption_key(obj, name))
            else:
                warnings.warn(f'Model anonymization discovered unreachable field {name} on model'
                              f'{obj.__class__.__name__} on obj {obj} with pk {obj.pk}')

    def deanonymize_obj(self, obj: Model, fields: Union[Fields, FieldMatrix] = '__ALL__',
                        base_encryption_key: Optional[str] = None):

        if not self.is_reversible(obj):
            raise self.IrreversibleAnonymizerException(f'{self.__class__.__name__} for obj "{obj}" is not reversible.')

        if base_encryption_key:
            self._base_encryption_key = base_encryption_key

        parsed_fields: Fields = Fields(fields, obj.__class__) if not isinstance(fields, Fields) else fields

        # Filter out already anonymized fields
        raw_local_fields = [i for i in parsed_fields.local_fields if
                            self.is_field_anonymized(obj, i) and self[i].get_is_reversible(obj)]
        update_dict = {name: self.get_deanonymized_value_from_obj(self[name], obj, name) for name in raw_local_fields}

        if self.anonymize_reversion(obj):
            from reversion.models import Version
            from gdpr.utils import get_reversion_versions, get_reversion_local_field_dict
            versions: List[Version] = get_reversion_versions(obj)
            versions_update_dict = [
                (
                    version,
                    {
                        name: self.get_deanonymized_value_from_version(self[name], obj, version, name)
                        for name in raw_local_fields
                        if name in get_reversion_local_field_dict(version)
                    }
                )
                for version in versions
            ]
            self.perform_deanonymization_with_version(obj, update_dict, versions_update_dict)
        else:
            self.perform_deanonymization(obj, update_dict)

        for name, related_fields in parsed_fields.related_fields.items():
            related_attribute = getattr(obj, name, None)
            related_metafield = getattr(obj.__class__, name, None)
            if self.is_reverse_relation(related_metafield):
                for related_obj in related_attribute.all():
                    related_fields.anonymizer.deanonymize_obj(
                        related_obj, related_fields,
                        base_encryption_key=self._get_encryption_key(obj, name))
            elif self.is_forward_relation(related_metafield) and related_attribute is not None:
                related_fields.anonymizer.deanonymize_obj(
                    related_attribute, related_fields,
                    base_encryption_key=self._get_encryption_key(obj, name))
            elif related_attribute is None and related_metafield is None:
                if self.is_generic_relation(getattr(self, name, None)):
                    objs = getattr(self, name).get_related_objects(obj)
                    for related_obj in objs:
                        related_fields.anonymizer.deanonymize_obj(
                            related_obj, related_fields,
                            base_encryption_key=self._get_encryption_key(obj, name))
            else:
                warnings.warn(f'Model anonymization discovered unreachable field {name} on model'
                              f'{obj.__class__.__name__} on obj {obj} with pk {obj.pk}')


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

    def anonymize_obj(self, obj: Model, legal_reason: Optional[LegalReason] = None,
                      purpose: Optional["AbstractPurpose"] = None,
                      fields: Union[Fields, FieldMatrix] = '__ALL__', base_encryption_key: Optional[str] = None):
        obj.__class__.objects.filter(pk=obj.pk).delete()

    def anonymize_qs(self, qs):
        qs.delete()
