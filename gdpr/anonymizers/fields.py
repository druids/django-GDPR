from datetime import timedelta
from decimal import Decimal
from typing import Any, Callable, Optional, Union

from django.core.exceptions import ImproperlyConfigured
from unidecode import unidecode

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import (
    decrypt_email_address, decrypt_text, encrypt_email_address, encrypt_text, numerize_key, translate_iban,
    translate_text
)
from gdpr.ipcypher import decrypt_ip, encrypt_ip
from gdpr.utils import get_number_guess_len


class FunctionFieldAnonymizer(FieldAnonymizer):
    """
    Use this field anonymization for defining in place lambda anonymization method.

    Example:
    ```
    secret_code = FunctionFieldAnonymizer(lambda self, x, key: x**2)
    ```

    If you want to supply anonymization and deanonymization you can do following:
    ```
    secret_code = FunctionFieldAnonymizer(
        func=lambda self, x, key: x**2+self.get_numeric_encryption_key(key),
        deanonymize_func=lambda a, x, key: x**2-a.get_numeric_encryption_key(key)
        )
    ```
    """

    anon_func: Callable
    deanonymize_func: Optional[Callable] = None
    max_anonymization_range: int

    def __init__(self,
                 anon_func: Union[Callable[[Any, Any], Any], Callable[["FunctionFieldAnonymizer", Any, Any], Any]],
                 deanonymize_func: Callable[["FunctionFieldAnonymizer", Any, Any], Any] = None,
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if callable(anon_func):
            self.anon_func = anon_func  # type: ignore
        else:
            raise ImproperlyConfigured('Supplied func is not callable.')

        if callable(deanonymize_func):
            self.deanonymize_func = deanonymize_func
        elif deanonymize_func is not None:
            raise ImproperlyConfigured('Supplied deanonymize_func is not callable.')

    def get_numeric_encryption_key(self, encryption_key: str) -> int:
        return numerize_key(encryption_key) % self.max_anonymization_range

    def get_encrypted_value(self, value, encryption_key: str):
        if self.deanonymize_func is None:
            return self.anon_func(value, encryption_key)
        else:
            return self.anon_func(self, value, encryption_key)

    def get_is_reversible(self, obj=None, raise_exception: bool = False):
        is_reversible = self.deanonymize_func is not None
        if not is_reversible:
            raise self.IrreversibleAnonymizationException
        return is_reversible

    def get_decrypted_value(self, value, encryption_key: str):
        if not self.get_is_reversible():
            raise self.IrreversibleAnonymizationException()
        else:
            return self.deanonymize_func(self, value, encryption_key)  # type: ignore


class DateTimeFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for DateTimeField.

    """

    max_anonymization_range = 365 * 24 * 60 * 60

    def get_encrypted_value(self, value, encryption_key: str):
        return value - timedelta(seconds=self.get_numeric_encryption_key(encryption_key))

    def get_decrypted_value(self, value, encryption_key: str):
        return value + timedelta(seconds=self.get_numeric_encryption_key(encryption_key))


class DateFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for DateField.

    """

    max_anonymization_range = 365

    def get_encrypted_value(self, value, encryption_key: str):
        return value - timedelta(days=self.get_numeric_encryption_key(encryption_key))

    def get_decrypted_value(self, value, encryption_key: str):
        return value + timedelta(days=self.get_numeric_encryption_key(encryption_key))


class CharFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    transliterate - The CharFieldAnonymizer encrypts only ASCII chars and non-ascii chars are left the same e.g.:
    `François` -> `rbTTç]3d` if True the original text is transliterated e.g. `François` -> 'Francois' -> `rbTTQ9Zg`.
    """

    transliterate = False

    def __init__(self, *args, transliterate: bool = False, **kwargs):
        self.transliterate = transliterate
        super().__init__(*args, **kwargs)

    def get_encrypted_value(self, value, encryption_key: str):
        return encrypt_text(encryption_key, value if not self.transliterate else unidecode(value))

    def get_decrypted_value(self, value, encryption_key: str):
        return decrypt_text(encryption_key, value)


class EmailFieldAnonymizer(FieldAnonymizer):

    def get_encrypted_value(self, value, encryption_key: str):
        return encrypt_email_address(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key: str):
        return decrypt_email_address(encryption_key, value)


class DecimalFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for CharField.
    """

    max_anonymization_range = 10000
    decimal_places: int = 2

    def get_offset(self, encryption_key: str):
        return Decimal(self.get_numeric_encryption_key(encryption_key)) / Decimal(10 ** self.decimal_places)

    def get_encrypted_value(self, value, encryption_key: str):
        return value + self.get_offset(encryption_key)

    def get_decrypted_value(self, value, encryption_key: str):
        return value - self.get_offset(encryption_key)


class IPAddressFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for GenericIPAddressField.

    Works for both ipv4 and ipv6.
    """

    def get_encrypted_value(self, value, encryption_key: str):
        return encrypt_ip(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key: str):
        return decrypt_ip(encryption_key, value)


class IBANFieldAnonymizer(FieldAnonymizer):
    """
    Field anonymizer for International Bank Account Number.
    """

    def get_decrypted_value(self, value: Any, encryption_key: str):
        return translate_iban(encryption_key, value)

    def get_encrypted_value(self, value: Any, encryption_key: str):
        return translate_iban(encryption_key, value, False)


class JSONFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for JSONField.
    """

    def get_numeric_encryption_key(self, encryption_key: str, value: Union[int, float] = None) -> int:
        if value is None:
            return numerize_key(encryption_key)
        return numerize_key(encryption_key) % 10 ** get_number_guess_len(value)

    def anonymize_json_value(self, value: Union[list, dict, bool, None, str, int, float],
                             encryption_key: str,
                             anonymize: bool = True) -> Union[list, dict, bool, None, str, int, float]:
        if value is None:
            return None
        elif type(value) is str:
            return translate_text(encryption_key, value, anonymize)  # type: ignore
        elif type(value) is int:
            return value + self.get_numeric_encryption_key(encryption_key, value) * (  # type: ignore
                1 if anonymize else -1)
        elif type(value) is float:
            # 9.14 - 3.14 -> 3.1400000000000006 - (To avoid this we are using Decimal)
            return float(
                Decimal(str(value)) + self.get_numeric_encryption_key(encryption_key, value) * (  # type: ignore
                    1 if anonymize else -1))
        elif type(value) is dict:
            return {key: self.anonymize_json_value(item, encryption_key, anonymize) for key, item in
                    value.items()}  # type: ignore
        elif type(value) is list:
            return [self.anonymize_json_value(item, encryption_key, anonymize) for item in value]  # type: ignore
        elif type(value) is bool and self.get_numeric_encryption_key(encryption_key) % 2 == 0:
            return not value
        return value

    def get_encrypted_value(self, value, encryption_key: str):
        return self.anonymize_json_value(value, encryption_key)

    def get_decrypted_value(self, value, encryption_key: str):
        return self.anonymize_json_value(value, encryption_key, anonymize=False)


class StaticValueFieldAnonymizer(FieldAnonymizer):
    """
    Static value anonymizer replaces value with defined static value.
    """
    is_reversible = False

    def __init__(self, value: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value: Any = value

    def get_encrypted_value(self, value: Any, encryption_key: str) -> Any:
        return self.value


class SiteIDUsernameFieldAnonymizer(FieldAnonymizer):
    """
    Encrypts username in format 1:foo@bar.com
    """

    def get_encrypted_value(self, value, encryption_key: str):
        split = value.split(':', 1)
        if len(split) == 2:
            return f'{split[0]}:{encrypt_email_address(encryption_key, split[1])}'
        return encrypt_email_address(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key: str):
        split = value.split(':', 1)
        if len(split) == 2:
            return f'{split[0]}:{decrypt_email_address(encryption_key, split[1])}'
        return decrypt_email_address(encryption_key, value)
