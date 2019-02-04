from typing import Any, List, Iterable, Optional, TYPE_CHECKING, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from gdpr.encryption import numerize_key

if TYPE_CHECKING:
    from gdpr.anonymizers import ModelAnonymizer


class RelationAnonymizer:
    """
    Base class for Anonymizers defining special relations.
    """

    def get_related_objects(self) -> Iterable:
        raise NotImplementedError


class FieldAnonymizer:
    """
    Field anonymizer's purpose is to anonymize model field according to defined rule.
    """

    ignore_empty_values: bool = True
    empty_values: List[Any] = [None]
    _encryption_key = None
    is_reversible: bool = True

    def __init__(self, ignore_empty_values: bool = None, empty_values: Optional[List[Any]] = None):
        """
        Args:
            ignore_empty_values: defines if empty value of a model will be ignored or should be anonymized too
            empty_values: define list of values which are considered as empty
        """
        self._ignore_empty_values = ignore_empty_values if ignore_empty_values is not None else self.ignore_empty_values
        self._empty_values = empty_values if empty_values is not None else self.empty_values

    def get_anonymized_value_from_obj(self, obj, name: str, encryption_key: Optional[str] = None):
        value = getattr(obj, name)
        if self._ignore_empty_values and value in self._empty_values:
            return value
        self._encryption_key = encryption_key
        return self.get_anonymized_value(value)

    def get_encryption_key(self):
        """Return encryption key to use.

        Override this method for custom logic.
        """
        if self._encryption_key is None:
            raise ImproperlyConfigured()
        return self._encryption_key

    def get_anonymized_value(self, value: Any) -> Any:
        """
        There must be defined implementation of rule for anonymization.
        To retain compatibility with older anonymizers this method is used as redirect to
        `get_encrypted_value`.

        Args:
            value: value that is anonymize

        Returns:
            anonymized value
        """
        return self.get_encrypted_value(value)

    def get_encrypted_value(self, value: Any) -> Any:
        """
        There must be defined implementation of rule for anonymization

        Args:
            value: value that is anonymize

        Returns:
            anonymized value
        """
        raise NotImplementedError

    def get_decrypted_value(self, value: Any) -> Any:
        """
        There must be defined implementation of rule for anonymization

        Args:
            value: value that is anonymize

        Returns:
            anonymized value
        """
        if self.is_reversible:
            raise NotImplementedError
        return value


class NumericFieldAnonymizer(FieldAnonymizer):
    max_anonymization_range: int

    def __init__(self, max_anonymization_range: int = None, ignore_empty_values: bool = None,
                 empty_values: Optional[List[Any]] = None):
        if max_anonymization_range:
            self.max_anonymization_range = max_anonymization_range
        super().__init__(ignore_empty_values, empty_values)

    def get_numeric_encryption_key(self, value: Union[int, float] = None) -> int:
        if value is None:
            return numerize_key(self.get_encryption_key()) % self.max_anonymization_range
        # safety measure against key getting one bigger (overflow) on decrypt e.g. (5)=1 -> 5 + 8 = 13 -> (13)=2
        guess_len = len(str(int(value)))
        return numerize_key(self.get_encryption_key()) % 10 ** (guess_len if guess_len % 2 != 0 else (guess_len - 1))



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
