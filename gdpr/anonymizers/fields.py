import re
import warnings
from collections import namedtuple
from datetime import timedelta
from decimal import Decimal
from typing import Any, Callable, Optional, List, Union

from django.core.exceptions import ImproperlyConfigured

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import (
    encrypt_message, decrypt_message, encrypt_email, decrypt_email, numerize_key, NUMBERS, translate_message)
from gdpr.ipcypher import encrypt_ip, decrypt_ip


class FunctionFieldAnonymizer(FieldAnonymizer):
    """
    Use this field anonymization for defining in place lambda anonymization method.

    Example:
    ```
    secret_code = FunctionFieldAnonymizer(lambda x: x**2)
    ```

    If you want to supply anonymization and deanonymization you can do following:
    ```
    secret_code = FunctionFieldAnonymizer(
        func=lambda self, x: x**2+self.get_numeric_encryption_key(),
        deanonymize_func=lambda a, x: x**2-a.get_numeric_encryption_key()
        )
    ```
    """

    anon_func: Callable
    deanonymize_func: Optional[Callable] = None
    max_anonymization_range: int

    def __init__(self,
                 anon_func: Union[Callable[[Any], Any], Callable[["FunctionFieldAnonymizer", Any], Any]],
                 deanonymize_func: Callable[["FunctionFieldAnonymizer", Any], Any] = None,
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

    def get_numeric_encryption_key(self) -> int:
        return numerize_key(self.get_encryption_key()) % self.max_anonymization_range

    def get_encrypted_value(self, value):
        if self.deanonymize_func is None:
            return self.anon_func(value)
        else:
            return self.anon_func(self, value)

    def get_is_reversible(self, obj=None):
        return self.deanonymize_func is not None

    def get_decrypted_value(self, value):
        if not self.get_is_reversible():
            raise self.IrreversibleAnonymizationException()
        else:
            return self.deanonymize_func(self, value)


class DateFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for DateField.

    """

    max_anonymization_range = 365 * 24 * 60 * 60

    def get_encrypted_value(self, value):
        return value - timedelta(seconds=self.get_numeric_encryption_key())

    def get_decrypted_value(self, value):
        return value + timedelta(seconds=self.get_numeric_encryption_key())


class CharFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for CharField.

    """

    def get_encrypted_value(self, value):
        return encrypt_message(self.get_encryption_key(), value)

    def get_decrypted_value(self, value):
        return decrypt_message(self.get_encryption_key(), value)


class EmailFieldAnonymizer(FieldAnonymizer):

    def get_encrypted_value(self, value):
        return encrypt_email(self.get_encryption_key(), value)

    def get_decrypted_value(self, value):
        return decrypt_email(self.get_encryption_key(), value)


class DecimalFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for CharField.
    """

    max_anonymization_range = 10000
    decimal_fields: int = 2

    def get_encrypted_value(self, value):
        return value + Decimal(self.get_numeric_encryption_key()) / Decimal(10 ** self.decimal_fields)

    def get_decrypted_value(self, value):
        return value - Decimal(self.get_numeric_encryption_key()) / Decimal(10 ** self.decimal_fields)


class IPAddressFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for GenericIPAddressField.

    Works for both ipv4 and ipv6.
    """

    def get_encrypted_value(self, value):
        return encrypt_ip(self.get_encryption_key(), value)

    def get_decrypted_value(self, value):
        return decrypt_ip(self.get_encryption_key(), value)


AccountNumber = namedtuple('AccountNumber', ['pre_num', 'num', 'bank'])


class AccountNumberFieldAnonymizer(FieldAnonymizer):
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

    def get_encrypted_value(self, value):
        account = self.parse_value(value)

        encrypted_account_num = encrypt_message(self.get_encryption_key(), account.num, NUMBERS)

        if account.pre_num:
            return f'{account.pre_num}-{encrypted_account_num}/{account.bank}'
        else:
            return f'{encrypted_account_num}/{account.bank}'

    def get_decrypted_value(self, value: Any):
        account = self.parse_value(value)

        decrypted_account_num = decrypt_message(self.get_encryption_key(), account.num, NUMBERS)

        if account.pre_num:
            return f'{account.pre_num}-{decrypted_account_num}/{account.bank}'
        else:
            return f'{decrypted_account_num}/{account.bank}'


class JSONFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization for JSONField.
    """

    def get_numeric_encryption_key(self, value: Union[int, float] = None) -> int:
        if value is None:
            return numerize_key(self.get_encryption_key())
        # safety measure against key getting one bigger (overflow) on decrypt e.g. (5)=1 -> 5 + 8 = 13 -> (13)=2
        guess_len = len(str(int(value)))
        return numerize_key(self.get_encryption_key()) % 10 ** (guess_len if guess_len % 2 != 0 else (guess_len - 1))

    def anonymize_json_value(self, value: Union[list, dict, bool, None, str, int, float],
                             anonymize: bool = True) -> Union[list, dict, bool, None, str, int, float]:
        if value is None:
            return None
        if type(value) is str:
            return translate_message(self.get_encryption_key(), value, anonymize)  # type: ignore
        if type(value) is int:
            return value + self.get_numeric_encryption_key(value) * (1 if anonymize else -1)  # type: ignore
        if type(value) is float:
            # 9.14 - 3.14 -> 3.1400000000000006 - (To avoid this we are using Decimal)
            return float(
                Decimal(str(value)) + self.get_numeric_encryption_key(value) * (1 if anonymize else -1))  # type: ignore
        if type(value) in [dict, list]:
            return self.anonymize_json(value, anonymize)  # type: ignore
        if type(value) is bool and self.get_numeric_encryption_key() % 2 == 0:
            return not value
        return value

    def anonymize_json(self, json: Union[list, dict], anonymize: bool = True) -> Union[list, dict]:
        if type(json) == dict:
            return {key: self.anonymize_json_value(value, anonymize) for key, value in json.items()}  # type: ignore
        elif type(json) == list:
            return [self.anonymize_json_value(value, anonymize) for value in json]
        raise ValueError

    def get_anonymized_value(self, value):
        warnings.warn('JSONFieldAnonymizer is not yet implemented.', UserWarning)
        return value


class StaticValueAnonymizer(FieldAnonymizer):
    """
    Static value anonymizer replaces value with defined static value.
    """
    is_reversible = False

    def __init__(self, value: Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value: Any = value

    def get_anonymized_value(self, value: Any) -> Any:
        return self.value
