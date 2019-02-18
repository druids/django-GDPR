import re
from collections import namedtuple
from datetime import timedelta
from decimal import Decimal
from typing import Any, Callable, Optional, Union

from django.core.exceptions import ImproperlyConfigured

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import (
    NUMBERS, decrypt_email, decrypt_message, encrypt_email, encrypt_message, numerize_key, translate_IBAN,
    translate_message
)
from gdpr.ipcypher import decrypt_ip, encrypt_ip


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
        else:
            self.is_reversible = False

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


class DateFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for DateField.

    """

    max_anonymization_range = 365 * 24 * 60 * 60

    def get_encrypted_value(self, value, encryption_key: str):
        return value - timedelta(seconds=self.get_numeric_encryption_key(encryption_key))

    def get_decrypted_value(self, value, encryption_key: str):
        return value + timedelta(seconds=self.get_numeric_encryption_key(encryption_key))


class CharFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    """

    def get_encrypted_value(self, value, encryption_key: str):
        return encrypt_message(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key: str):
        return decrypt_message(encryption_key, value)


class EmailFieldAnonymizer(FieldAnonymizer):

    def get_encrypted_value(self, value, encryption_key: str):
        return encrypt_email(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key: str):
        return decrypt_email(encryption_key, value)


class DecimalFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for CharField.
    """

    max_anonymization_range = 10000
    decimal_fields: int = 2

    def get_encrypted_value(self, value, encryption_key: str):
        return value + Decimal(self.get_numeric_encryption_key(encryption_key)) / Decimal(10 ** self.decimal_fields)

    def get_decrypted_value(self, value, encryption_key: str):
        return value - Decimal(self.get_numeric_encryption_key(encryption_key)) / Decimal(10 ** self.decimal_fields)


class IPAddressFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for GenericIPAddressField.

    Works for both ipv4 and ipv6.
    """

    def get_encrypted_value(self, value, encryption_key: str):
        return encrypt_ip(encryption_key, value)

    def get_decrypted_value(self, value, encryption_key: str):
        return decrypt_ip(encryption_key, value)


AccountNumber = namedtuple('AccountNumber', ['pre_num', 'num', 'bank'])


class CzechAccountNumberFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for czech account number.
    """

    def parse_value(self, value) -> AccountNumber:
        """

        :param value:
        :return: (predcisli)-(cislo)/(kod_banky)
        """
        account = re.match('(([0-9]{0,6})-)?([0-9]{1,10})/([0-9]{4})', value)
        return AccountNumber(account[2], account[3], account[4])  # type: ignore

    def get_encrypted_value(self, value, encryption_key: str):
        account = self.parse_value(value)

        encrypted_account_num = encrypt_message(encryption_key, account.num, NUMBERS)

        if account.pre_num:
            return f'{account.pre_num}-{encrypted_account_num}/{account.bank}'
        else:
            return f'{encrypted_account_num}/{account.bank}'

    def get_decrypted_value(self, value: Any, encryption_key: str):
        account = self.parse_value(value)

        decrypted_account_num = decrypt_message(encryption_key, account.num, NUMBERS)

        if account.pre_num:
            return f'{account.pre_num}-{decrypted_account_num}/{account.bank}'
        else:
            return f'{decrypted_account_num}/{account.bank}'


class IBANFieldAnonymizer(FieldAnonymizer):
    """
    Field anonymizer for International Bank Account Number.
    """

    def get_decrypted_value(self, value: Any, encryption_key: str):
        return translate_IBAN(encryption_key, value)

    def get_encrypted_value(self, value: Any, encryption_key: str):
        return translate_IBAN(encryption_key, value, False)


class JSONFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for JSONField.
    """

    def get_numeric_encryption_key(self, encryption_key: str, value: Union[int, float] = None) -> int:
        if value is None:
            return numerize_key(encryption_key)
        # safety measure against key getting one bigger (overflow) on decrypt e.g. (5)=1 -> 5 + 8 = 13 -> (13)=2
        guess_len = len(str(int(value)))
        return numerize_key(encryption_key) % 10 ** (guess_len if guess_len % 2 != 0 else (guess_len - 1))

    def anonymize_json_value(self, value: Union[list, dict, bool, None, str, int, float],
                             encryption_key: str,
                             anonymize: bool = True) -> Union[list, dict, bool, None, str, int, float]:
        if value is None:
            return None
        if type(value) is str:
            return translate_message(encryption_key, value, anonymize)  # type: ignore
        if type(value) is int:
            return value + self.get_numeric_encryption_key(encryption_key, value) * (  # type: ignore
                1 if anonymize else -1)
        if type(value) is float:
            # 9.14 - 3.14 -> 3.1400000000000006 - (To avoid this we are using Decimal)
            return float(
                Decimal(str(value)) + self.get_numeric_encryption_key(encryption_key, value) * (  # type: ignore
                    1 if anonymize else -1))
        if type(value) in [dict, list]:
            return self.anonymize_json(value, encryption_key, anonymize)  # type: ignore
        if type(value) is bool and self.get_numeric_encryption_key(encryption_key) % 2 == 0:
            return not value
        return value

    def anonymize_json(self, json: Union[list, dict], encryption_key: str, anonymize: bool = True) -> Union[list, dict]:
        if type(json) == dict:
            return {key: self.anonymize_json_value(value, encryption_key, anonymize) for key, value in
                    json.items()}  # type: ignore
        elif type(json) == list:
            return [self.anonymize_json_value(value, encryption_key, anonymize) for value in json]
        raise ValueError

    def get_encrypted_value(self, value, encryption_key: str):
        return self.anonymize_json(value, encryption_key)

    def get_decrypted_value(self, value, encryption_key: str):
        return self.anonymize_json(value, encryption_key, anonymize=False)


class StaticValueAnonymizer(FieldAnonymizer):
    """
    Static value anonymizer replaces value with defined static value.
    """
    is_reversible = False

    def __init__(self, value: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value: Any = value

    def get_encrypted_value(self, value: Any, encryption_key: str) -> Any:
        return self.value
