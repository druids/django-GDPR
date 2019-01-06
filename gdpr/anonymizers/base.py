from typing import Any, List, Optional


class FieldAnonymizer:
    """
    Field anonymizer's purpose is to anonymize model field accoding to defined rule.
    """

    ignore_empty_values: bool = True
    empty_values: List[Any] = [None]

    def __init__(self, ignore_empty_values: bool = None, empty_values: Optional[List[Any]] = None):
        """
        Args:
            ignore_empty_values: defines if empty value of a model will be ignored or should be anonymized too
            empty_values: define list of values which are considered as empty
        """
        self._ignore_empty_values = ignore_empty_values if ignore_empty_values is not None else self.ignore_empty_values
        self._empty_values = empty_values if empty_values is not None else self.empty_values

    def get_anonymized_value_from_obj(self, obj, name: str):
        value = getattr(obj, name)
        if self._ignore_empty_values and value in self._empty_values:
            return value
        else:
            return self.get_anonymized_value(value)

    def get_anonymized_value(self, value) -> Any:
        """
        There must be defined implementation of rule for anonymization

        Args:
            value: value that is anonymized

        Returns:
            anonymized value
        """
        raise NotImplementedError


class ModelAnonymizerBase(type):
    """
    Metaclass for anonymizers. The main purpose of the metaclass is to register anonymizers and find field anonymizers
    defined in the class as attributes and store it to the fields property.
    """

    def __new__(cls, name, bases, attrs):
        from gdpr.loading import anonymizer_register

        new_obj = super(ModelAnonymizerBase, cls).__new__(cls, name, bases, attrs)

        # Also ensure initialization is only performed for subclasses of ModelAnonymizer
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelAnonymizerBase)]
        if not parents or not hasattr(new_obj, 'Meta') or getattr(new_obj.Meta, 'abstract', False):
            return new_obj

        fields = {}
        for name, obj in attrs.items():
            if isinstance(obj, FieldAnonymizer):
                fields[name] = obj
        new_obj.fields = fields
        anonymizer_register.register(new_obj.Meta.model, new_obj)
        return new_obj
