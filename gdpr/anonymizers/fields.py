import warnings
from datetime import timedelta
from typing import Any, Callable

from django.core.exceptions import ImproperlyConfigured

from gdpr.anonymizers.base import FieldAnonymizer


class FunctionAnonymizer(FieldAnonymizer):
    """
    Use this field anonymization for defining in place lambda anonymization method.

    Example:
    ```
    secret_code = FunctionFieldAnonymizer(lambda x: x**2)
    ```
    """

    func = None

    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if callable(func):
            self.function = func
        else:
            raise ImproperlyConfigured('Supplied function is not callable.')

    def get_anonymized_value(self, value):
        return self.func(value)


class DateFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for DateField.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn('DateFieldAnonymizer is not yet implemented.', UserWarning)
        return value + timedelta(days=7)


class CharFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn('CharFieldAnonymizer is not yet implemented.', UserWarning)
        return value + 'NotImplemented'


class DecimalFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn('DecimalFieldAnonymizer is not yet implemented.', UserWarning)
        return value + 1


class IPAddressFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn('IPAddressFieldAnonymizer is not yet implemented.', UserWarning)
        return value


class AccountNumberFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn('AccountNumberFieldAnonymizer is not yet implemented.', UserWarning)
        return 'ANON' + value[4:]


class JSONFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for JSONField.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn('JSONFieldAnonymizer is not yet implemented.', UserWarning)
        return value


class StaticValueAnonymizer(FieldAnonymizer):
    """
    Static value anonymizer replaces value with defined static value.
    """

    def __init__(self, value: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value: Any = value

    def get_anonymized_value(self, value: Any) -> Any:
        return self.value
