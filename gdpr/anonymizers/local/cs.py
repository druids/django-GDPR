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

    def check_account_format(self) -> bool:
        pre_num = "%06d" % (self.pre_num or 0)
        num = "0" * (10 - len(str(self.num))) + str(self.num)

        pre_num_valid = sum(map(lambda x: x[0] * x[1], zip(map(lambda x: int(x), pre_num), PRE_NUM_WEIGHTS))) % 11 == 0
        num_valid = sum(map(lambda x: x[0] * x[1], zip(map(lambda x: int(x), num), NUM_WEIGHTS))) % 11 == 0

        return num_valid and pre_num_valid

    def _brute_force_next(self):
        self.num += 1
        if len(str(self.num)) > 10:
            self.num = 0
        while not self.check_account_format():
            if len(str(self.num)) > 10:
                self.num = 0
            self.num += 1

    def brute_force_next(self, n: int):
        for i in range(n):
            self._brute_force_next()

        return self  # allow chaining

    def _brute_force_prev(self):
        self.num -= 1
        if self.num <= 0:
            self.num = int("9" * 10)
        while not self.check_account_format():
            if self.num <= 0:
                self.num = int("9" * 10)
            self.num -= 1

    def brute_force_prev(self, n: int):
        for i in range(n):
            self._brute_force_prev()

        return self  # allow chaining

    @classmethod
    def parse(cls, value: str) -> "CzechAccountNumber":
        """
        :param value:
        :return: AccountNumber(predcisli)-(cislo)/(kod_banky)
        """
        account = re.match('((?P<pre_num>[0-9]{0,6})-)?(?P<num>[0-9]{1,10})/(?P<bank_code>[0-9]{4})', value)
        if account:
            pre_num = account.group("pre_num")
            num = account.group("num")
            bank_code = account.group("bank_code")
            return cls(pre_num=pre_num, pre_num_len=len(pre_num or ""), num=num, num_len=len(num),
                       bank=bank_code, bank_len=len(bank_code))
        raise ValidationError(f'Str \'{value}\' does not appear to be czech account number.')

    def __str__(self):
        return ((f'{str(self.pre_num).rjust(self.pre_num_len, "0") if self.pre_num_len else self.pre_num}-'
                 if self.pre_num else ""
                 ) + f'{str(self.num).rjust(self.num_len, "0")}/{str(self.bank).rjust(self.bank_len, "0")}')


class CzechIBAN(CzechAccountNumber):
    has_spaces = False
    control_code: int

    def __init__(self, *args, has_spaces: bool = False, control_code: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_spaces = has_spaces
        if control_code is not None:
            self.control_code = control_code
        else:
            self._update_control_code()

    @classmethod
    def from_account(cls, value: "CzechAccountNumber") -> "CzechIBAN":
        return cls(num=value.num, bank=value.bank, pre_num=value.num)

    @classmethod
    def parse(cls, value: str) -> "CzechIBAN":
        """
        :param value:
        :return: AccountNumber(predcisli)-(cislo)/(kod_banky)
        """
        account = re.match(
            'CZ(?P<control_code>[0-9]{2}) ?(?P<bank_code>[0-9]{4}) ?'
            '(?P<pre_num>[0-9]{4} ?[0-9]{2})(?P<num>[0-9]{2} ?[0-9]{4} ?[0-9]{4})',
            value)

        if account:
            control_code = int(account.group("control_code"))
            bank_code = int(account.group("bank_code"))
            pre_num = int(account.group("pre_num").replace(" ", ""))
            num = int(account.group("num").replace(" ", ""))

            return cls(
                control_code=control_code, has_spaces=" " in value,
                pre_num=pre_num, num=num, bank=bank_code)
        raise ValidationError(f'IBAN \'{value}\' does not appear to be czech IBAN.')

    def _to_str(self, spaces: Optional[bool] = None):
        pre_num = str(self.pre_num).rjust(6, "0")
        num = str(self.num).rjust(10, "0")
        out = (f'CZ{str(self.control_code).rjust(2, "0")} {str(self.bank).rjust(4, "0")} {pre_num[:4]} '
               f'{pre_num[4:]}{num[:2]} {num[2:6]} {num[6:]}')
        if (spaces is None and self.has_spaces) or spaces:
            return out
        return out.replace(" ", "")

    def __str__(self) -> str:
        return self._to_str()

    def _to_int(self) -> int:
        """
        Convert IBAN to numeric value (ISO 7064) to be able to calculate `control_code`and check if IBAN is valid.
        """
        iban = self._to_str(spaces=False)
        return int(
            "".join([i if not ord('A') <= ord(i) <= ord('Z') else str(ord(i) - 55) for i in iban[4:] + iban[:4]]))

    def check_iban_format(self) -> bool:
        return self._to_int() % 97 == 1

    def _update_control_code(self):
        """
        Calculate new control code
        """
        self.control_code = 0
        self.control_code = 98 - (self._to_int() % 97)

    def brute_force_next(self, n: int):
        self.control_code = 0
        super().brute_force_next(n)
        self._update_control_code()

        return self  # allow chaining

    def brute_force_prev(self, n: int):
        self.control_code = 0
        super().brute_force_prev(n)
        self._update_control_code()

        return self  # allow chaining


PRE_NUM_WEIGHTS = [10, 5, 8, 4, 2, 1]
NUM_WEIGHTS = [6, 3, 7, 9, 10, 5, 8, 4, 2, 1]


class CzechAccountNumberFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymization for czech account number.

    Setting `use_smart_method=True` retains valid format for encrypted value using this
    have significant effect on performance.
    """
    use_smart_method = False
    max_anonymization_range = 10000

    def __init__(self, *args, use_smart_method=False, **kwargs):
        self.use_smart_method = use_smart_method
        super().__init__(*args, **kwargs)

    def get_encrypted_value(self, value, encryption_key: str):
        account = CzechAccountNumber.parse(value)

        if self.use_smart_method and account.check_account_format():
            return str(account.brute_force_next(self.get_numeric_encryption_key(encryption_key)))

        account.num = int(encrypt_message(encryption_key, str(account.num), NUMBERS))

        return str(account)

    def get_decrypted_value(self, value: Any, encryption_key: str):
        account = CzechAccountNumber.parse(value)

        if self.use_smart_method and account.check_account_format():
            return str(account.brute_force_prev(self.get_numeric_encryption_key(encryption_key)))

        account.num = int(decrypt_message(encryption_key, str(account.num), NUMBERS))

        return str(account)


class CzechIBANSmartFieldAnonymizer(NumericFieldAnonymizer):
    max_anonymization_range = 10000

    def get_encrypted_value(self, value: Any, encryption_key: str):
        iban = CzechIBAN.parse(value)
        if not iban.check_iban_format():
            raise ValidationError(f'IBAN \'{value}\' does not appear to be valid czech IBAN.')
        return str(iban.brute_force_next(self.get_numeric_encryption_key(encryption_key)))

    def get_decrypted_value(self, value: Any, encryption_key: str):
        iban = CzechIBAN.parse(value)
        if not iban.check_iban_format():
            raise ValidationError(f'IBAN \'{value}\' does not appear to be valid czech IBAN.')
        return str(iban.brute_force_prev(self.get_numeric_encryption_key(encryption_key)))


class CzechPhoneNumberFieldAnonymizer(FieldAnonymizer):

    def split_phone_number(self, value: str) -> Tuple[str, str]:
        """
        Split phone number in international format into area code and number
        """
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
