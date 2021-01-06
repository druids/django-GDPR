from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Type, Union

from django.db.models import Model

from gdpr.loading import anonymizer_register

FieldMatrix = Union[str, Tuple[Any, ...]]
FieldList = Union[List[str], str]
RelatedFieldDict = Dict[str, "Fields"]

if TYPE_CHECKING:
    from gdpr.anonymizers import ModelAnonymizer


class Fields:
    local_fields: FieldList
    related_fields: RelatedFieldDict
    anonymizer: "ModelAnonymizer"
    model: Type[Model]

    def __init__(self, fields: FieldMatrix, model: Type[Model], anonymizer_instance: "ModelAnonymizer" = None):
        self.model = model
        self.anonymizer = anonymizer_register[self.model]() if anonymizer_instance is None else anonymizer_instance
        self.local_fields = self.parse_local_fields(fields)
        self.related_fields = self.parse_related_fields(fields)

    def parse_local_fields(self, fields: FieldMatrix) -> FieldList:
        """Get Iterable of local fields from fields matrix."""
        if fields == '__ALL__' or ('__ALL__' in fields and type(fields) != str):
            return list(self.anonymizer.keys())

        return [field for field in fields if type(field) == str]

    def parse_related_fields(self, fields: FieldMatrix) -> RelatedFieldDict:
        """Get Dictionary of related fields from fields matrix."""
        out_dict = {}
        for name, related_fields in [field_tuple for field_tuple in fields if isinstance(field_tuple, (list, tuple))]:
            out_dict[name] = Fields(related_fields, self.anonymizer.get_related_model(name))

        return out_dict

    def get_tuple(self) -> FieldMatrix:
        return (*self.local_fields, *[(name, fields.get_tuple()) for name, fields in self.related_fields.items()])

    def __len__(self):
        return len(self.local_fields) + len(self.related_fields)

    def __isub__(self, other: "Fields") -> "Fields":
        self.local_fields = [field for field in self.local_fields if field not in other.local_fields]

        for name, related_fields in self.related_fields.items():
            if name in other.related_fields:
                related_fields -= other.related_fields[name]

        for name in list(self.related_fields.keys()):
            if len(self.related_fields[name]) == 0:
                del self.related_fields[name]

        return self
