import re
from collections import namedtuple
from typing import Any, Tuple

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import encrypt_message, decrypt_message, NUMBERS

AccountNumber = namedtuple('AccountNumber', ['pre_num', 'num', 'bank'])

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

    def check_account_format(self, value: AccountNumber) -> bool:
        pre_num = "%06d" % int(value.pre_num or 0)
        num = "0" * (10 - len(value.num)) + value.num

        pre_num_valid = sum(map(lambda x: x[0] * x[1], zip(map(lambda x: int(x), pre_num), PRE_NUM_WEIGHTS))) % 11 == 0
        num_valid = sum(map(lambda x: x[0] * x[1], zip(map(lambda x: int(x), num), NUM_WEIGHTS))) % 11 == 0

        return num_valid and pre_num_valid

    def parse_value(self, value) -> AccountNumber:
        """

        :param value:
        :return: (predcisli)-(cislo)/(kod_banky)
        """
        account = re.match('(([0-9]{0,6})-)?([0-9]{1,10})/([0-9]{4})', value)
        return AccountNumber(account[2], account[3], account[4])  # type: ignore

    def _brute_force_next(self, value: AccountNumber) -> AccountNumber:
        new_value = int(value.num) + 1
        if len(str(new_value)) > 10:
            new_value = 0
        while not self.check_account_format((lambda x: AccountNumber(value.pre_num, str(x), value.bank))(new_value)):
            if len(str(new_value)) > 10:
                new_value = 0
            new_value += 1

        return AccountNumber(value.pre_num, "0" * (10 - len(str(new_value))) + str(new_value), value.bank)

    def brute_force_next(self, value: AccountNumber, n: int) -> AccountNumber:
        new_value = value
        for i in range(n):
            new_value = self._brute_force_next(new_value)
        return new_value

    def _brute_force_prev(self, value: AccountNumber) -> AccountNumber:
        new_value = int(value.num) - 1
        if new_value <= 0:
            new_value = int("9" * 10)
        while not self.check_account_format((lambda x: AccountNumber(value.pre_num, str(x), value.bank))(new_value)):
            if new_value <= 0:
                new_value = int("9" * 10)
            new_value -= 1

        return AccountNumber(value.pre_num, "0" * (10 - len(str(new_value))) + str(new_value), value.bank)

    def brute_force_prev(self, value: AccountNumber, n: int) -> AccountNumber:
        new_value = value
        for i in range(n):
            new_value = self._brute_force_prev(new_value)
        return new_value

    def str_account_number(self, account: AccountNumber) -> str:
        if account.pre_num:
            return f'{account.pre_num}-{account.num}/{account.bank}'
        else:
            return f'{account.num}/{account.bank}'

    def get_encrypted_value(self, value, encryption_key: str):
        account = self.parse_value(value)

        if self.use_smart_method and self.check_account_format(account):
            return self.str_account_number(
                self.brute_force_next(account, self.get_numeric_encryption_key(encryption_key)))

        encrypted_account_num = encrypt_message(encryption_key, account.num, NUMBERS)

        return self.str_account_number(AccountNumber(account.pre_num, encrypted_account_num, account.bank))

    def get_decrypted_value(self, value: Any, encryption_key: str):
        account = self.parse_value(value)

        if self.use_smart_method and self.check_account_format(account):
            return self.str_account_number(
                self.brute_force_prev(account, self.get_numeric_encryption_key(encryption_key)))

        decrypted_account_num = decrypt_message(encryption_key, account.num, NUMBERS)

        return self.str_account_number(AccountNumber(account.pre_num, decrypted_account_num, account.bank))


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
