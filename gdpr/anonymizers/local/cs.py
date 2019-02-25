import re
from typing import Any, Optional, Tuple, Union

from django.core.exceptions import ValidationError

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import NUMBERS, decrypt_message, encrypt_message


class CzechAccountNumber:
    pre_num: Optional[int]
    pre_num_len: Optional[int]
    num: int
    num_len: int = 10
    bank: int

    def __init__(self, num: Union[int, str], bank: Union[int, str], pre_num: Optional[Union[int, str]] = None,
                 num_len: int = 10, pre_num_len: Optional[int] = None, bank_len: int = 4):
        self.num = int(num)
        self.num_len = num_len
        self.bank = int(bank)
        self.bank_len = bank_len
        self.pre_num_len = pre_num_len
        self.pre_num = int(pre_num) if pre_num else None

    def check_format(self) -> bool:
        pre_num = "%06d" % (self.pre_num or 0)
        num = "0" * (10 - len(str(self.num))) + str(self.num)

        pre_num_valid = sum(map(lambda x: x[0] * x[1], zip(map(lambda x: int(x), pre_num), PRE_NUM_WEIGHTS))) % 11 == 0
        num_valid = sum(map(lambda x: x[0] * x[1], zip(map(lambda x: int(x), num), NUM_WEIGHTS))) % 11 == 0

        return num_valid and pre_num_valid

    def _brute_force_next(self):
        self.num += 1
        if len(str(self.num)) > 10:
            self.num = 0
        while not self.check_format():
            if len(str(self.num)) > 10:
                self.num = 0
            self.num += 1

    def brute_force_next(self, n: int):
        for i in range(n):
            self._brute_force_next()

    def _brute_force_prev(self):
        self.num -= 1
        if self.num <= 0:
            self.num = int("9" * 10)
        while not self.check_format():
            if self.num <= 0:
                self.num = int("9" * 10)
            self.num -= 1

    def brute_force_prev(self, n: int):
        for i in range(n):
            self._brute_force_prev()

    @classmethod
    def parse(cls, value: str) -> "CzechAccountNumber":
        """
        :param value:
        :return: AccountNumber(predcisli)-(cislo)/(kod_banky)
        """
        account = re.match('(([0-9]{0,6})-)?([0-9]{1,10})/([0-9]{4})', value)
        if account:
            return cls(pre_num=account[2], pre_num_len=len(account[2] or ""), num=account[3], num_len=len(account[3]),
                       bank=account[4], bank_len=len(account[4]))
        raise ValidationError(f'Str \'{value}\' does not appear to be czech account number.')

    def __str__(self):
        return ((f'{str(self.pre_num).rjust(self.pre_num_len, "0") if self.pre_num_len else self.pre_num}-'
                 if self.pre_num else ""
                 ) + f'{str(self.num).rjust(self.num_len, "0")}/{str(self.bank).rjust(self.bank_len, "0")}')


PRE_NUM_WEIGHTS = [10, 5, 8, 4, 2, 1]
NUM_WEIGHTS = [6, 3, 7, 9, 10, 5, 8, 4, 2, 1]


class CzechAccountNumberFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for czech account number.

    Setting `use_smart_method=True` retains valid format for encrypted value.
    """
    use_smart_method = False
    max_anonymization_range = 10000

    def __init__(self, *args, use_smart_method=False, **kwargs):
        self.use_smart_method = use_smart_method
        super().__init__(*args, **kwargs)

    def get_encrypted_value(self, value, encryption_key: str):
        account = CzechAccountNumber.parse(value)

        if self.use_smart_method and account.check_format():
            account.brute_force_next(self.get_numeric_encryption_key(encryption_key))
            return str(account)

        account.num = int(encrypt_message(encryption_key, str(account.num), NUMBERS))

        return str(account)

    def get_decrypted_value(self, value: Any, encryption_key: str):
        account = CzechAccountNumber.parse(value)

        if self.use_smart_method and account.check_format():
            account.brute_force_prev(self.get_numeric_encryption_key(encryption_key))
            return str(account)

        account.num = int(decrypt_message(encryption_key, str(account.num), NUMBERS))

        return str(account)


class CzechPhoneNumberAnonymizer(FieldAnonymizer):

    def split_phone_number(self, value: str) -> Tuple[str, str]:
        area_code = value[:-9]
        phone_number = value[-9:]
        return area_code, phone_number

    def get_encrypted_value(self, value: str, encryption_key: str):
        area_code, phone_number = self.split_phone_number(value)
        encrypted_phone_number = encrypt_message(encryption_key, phone_number[3:], NUMBERS)
        return f"{area_code}{phone_number[:3]}{encrypted_phone_number}"

    def get_decrypted_value(self, value: str, encryption_key: str):
        area_code, phone_number = self.split_phone_number(value)
        encrypted_phone_number = decrypt_message(encryption_key, phone_number[3:], NUMBERS)
        return f"{area_code}{phone_number[:3]}{encrypted_phone_number}"
