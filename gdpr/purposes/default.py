from collections import namedtuple
from typing import Any, Dict, Iterable, KeysView, List, Optional, TYPE_CHECKING, Tuple, Type, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, Q

from gdpr.loading import anonymizer_register, purpose_register

if TYPE_CHECKING:
    from gdpr.models import LegalReason
    from gdpr.anonymizers import ModelAnonymizer

FieldList = Union[List[str], Tuple, KeysView[str]]  # List, tuple or return of dict keys() method.
FieldMatrix = Union[str, Tuple[Any, ...]]
RelatedMatrix = Dict[str, FieldMatrix]
PurposesFieldMatrices = Iterable[FieldMatrix]
PurposesFieldLists = Iterable[FieldList]
PurposesRelatedFieldMatrices = Iterable[RelatedMatrix]
PurposesSplitFields = Iterable["PurposeSplitFields"]


class PurposeSplitFields(namedtuple('PurposeSplitFields', ['local', 'related'])):
    def __new__(_cls, local=tuple(), related=dict()):
        return super().__new__(_cls, local, related)

    def get_tuple(self):
        if type(self.local) == str:
            return (self.local, *tuple(self.related.items()))
        return (*self.local, *tuple(self.related.items()))


class PurposeMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        from gdpr.loading import purpose_register

        new_class = super().__new__(mcs, name, bases, attrs)
        if hasattr(new_class, 'slug') and new_class.slug:
            if new_class.slug in purpose_register:
                raise ImproperlyConfigured('More anonymization purposes with slug {}'.format(new_class.slug))

            purpose_register.register(new_class.slug, new_class)
        return new_class

    def __str__(self):
        return str(self.name)


class AbstractPurpose(metaclass=PurposeMetaclass):
    """

    :param anonymize_legal_reason_related_object_only: If True anonymize only related objects which have links which
    have LegalReasonRelatedObject records.
    """

    name: str
    slug: str
    fields: Union[str, Tuple[Any, ...]]
    expiration_timedelta: Any
    anonymize_legal_reason_related_objects_only: bool = False  # @TODO: Add support

    def get_local_fields(self, anonymizer: Type["ModelAnonymizer"], fields: FieldMatrix) -> FieldList:
        """Get Iterable of local fields from fields matrix."""
        if fields == "__ALL__":
            return anonymizer().keys()
        for i in fields:
            if type(i) not in [str, list, tuple]:
                raise ImproperlyConfigured()
        local_fields = [i for i in fields if type(i) == str]
        if "__ALL__" in local_fields:
            return anonymizer().keys()
        return local_fields

    def get_related_fields(self, fields: FieldMatrix) -> RelatedMatrix:
        """Get Dictionary of related fields from fields matrix."""
        related_fields = [i for i in fields if type(i) in [list, tuple]]
        for i in related_fields:
            if len(i) != 2:
                raise ImproperlyConfigured()
        return {i[0]: i[1] for i in related_fields}

    def split_fields(self, fields: FieldMatrix, model: Type[Model]) -> PurposeSplitFields:
        return PurposeSplitFields(self.get_local_fields(anonymizer_register[model], fields),
                                  self.get_related_fields(fields))

    def filter_local_fields(self, local: FieldList, others: PurposesSplitFields) -> FieldList:
        return [i for i in local if not any([i in j.local for j in others])]

    def filter_related_fields(self, related: RelatedMatrix, others: PurposesSplitFields,
                              model: Type[Model]) -> FieldMatrix:
        others_related_keys = set([rel for i in others for rel in i.related.keys()])
        for k in related.keys():
            if k not in others_related_keys:
                continue  # The best we don't have to do anything!
            others_actual = [i.related[k] for i in others if k in i.related]
            related_actual = related[k]
            related_model = getattr(model, k).rel.related_model
            related[k] = self.get_filtered_fields(related_model, related_actual, others_actual)

        # Filter out relations with no fields inside
        related = {k: v for k, v in related.items() if len(v) > 0}

        return tuple(related.items())

    def get_filtered_fields(self, model: Type[Model], fields: FieldMatrix,
                            other_fields: PurposesFieldMatrices) -> FieldMatrix:
        local_fields, related_fields = self.split_fields(fields, model)
        other_fields_split = [self.split_fields(i, model) for i in other_fields]

        return (*self.filter_local_fields(local_fields, other_fields_split),
                *self.filter_related_fields(related_fields, other_fields_split, model))

    def anonymize_obj(self, obj: Type[Model], legal_reason: Optional["LegalReason"] = None,
                      fields: Optional[FieldMatrix] = None):
        fields = fields or self.fields
        from gdpr.models import LegalReason  # noqa

        # MultiLegalReason
        other_legal_reasons = LegalReason.objects.filter_source_instance(obj).filter(is_active=True)
        if legal_reason:
            other_legal_reasons = other_legal_reasons.filter(~Q(pk=legal_reason.pk))
        if other_legal_reasons.count() == 0:
            anonymizer_register[obj.__class__]().anonymize_obj(obj, legal_reason, self, fields)
            return

        from gdpr.loading import purpose_register

        # Transform legal_reasons to fields
        allowed_field_matrices = [purpose_register[slug].fields for slug in
                                  set([i.purpose_slug for i in other_legal_reasons])]
        filtered_fields = self.get_filtered_fields(obj.__class__, fields, allowed_field_matrices)

        anonymizer_register[obj.__class__]().anonymize_obj(obj, legal_reason, self, filtered_fields)


purposes_map = purpose_register  # Backwards compatibility
