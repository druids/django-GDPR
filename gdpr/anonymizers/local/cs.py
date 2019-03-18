import datetime
import re
from typing import Any, Optional, Tuple, Union

from django.core.exceptions import ValidationError

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer
from gdpr.encryption import LETTERS_UPPER, NUMBERS, decrypt_text, encrypt_text

PRE_NUM_WEIGHTS = [10, 5, 8, 4, 2, 1]
NUM_WEIGHTS = [6, 3, 7, 9, 10, 5, 8, 4, 2, 1]


class CzechAccountNumber:
    pre_num: Optional[int]
    pre_num_len: Optional[int]
    num: int
    num_len: int = 10
    bank: int

    CZECH_ACCOUNT_RE = re.compile('((?P<pre_num>[0-9]{0,6})-)?(?P<num>[0-9]{1,10})/(?P<bank_code>[0-9]{4})')

    def __init__(self, num: Union[int, str], bank: Union[int, str], pre_num: Optional[Union[int, str]] = None,
                 num_len: int = 10, pre_num_len: Optional[int] = None, bank_len: int = 4):
        self.num = int(num)
        self.num_len = num_len
        self.bank = int(bank)
        self.bank_len = bank_len
        self.pre_num_len = pre_num_len
        self.pre_num = int(pre_num) if pre_num is not None and pre_num != 0 else None

    def check_account_format(self) -> bool:
        pre_num = "%06d" % (self.pre_num or 0)
        num = '0' * (10 - len(str(self.num))) + str(self.num)

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
            self.num = int('9' * 10)
        while not self.check_account_format():
            if self.num <= 0:
                self.num = int('9' * 10)
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
        account = re.match(cls.CZECH_ACCOUNT_RE, value)

        if account is None:
            raise ValidationError(f'Str \'{value}\' does not appear to be czech account number.')

        pre_num = account.group('pre_num')
        num = account.group('num')
        bank_code = account.group('bank_code')
        return cls(pre_num=pre_num, pre_num_len=len(pre_num or ""), num=num, num_len=len(num),
                   bank=bank_code, bank_len=len(bank_code))

    def __str__(self):
        return ((f'{str(self.pre_num).rjust(self.pre_num_len, "0") if self.pre_num_len else self.pre_num}-'
                 if self.pre_num else ''
                 ) + f'{str(self.num).rjust(self.num_len, "0")}/{str(self.bank).rjust(self.bank_len, "0")}')


class CzechIBAN(CzechAccountNumber):
    has_spaces = False
    control_code: int
    CZECH_IBAN_RE = re.compile(
        'CZ(?P<control_code>[0-9]{2}) ?(?P<bank_code>[0-9]{4}) ?'
        '(?P<pre_num>[0-9]{4} ?[0-9]{2})(?P<num>[0-9]{2} ?[0-9]{4} ?[0-9]{4})',
    )

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
        account = re.match(cls.CZECH_IBAN_RE, value)

        if account:
            control_code = account.group('control_code').upper()
            bank_code = account.group('bank_code').upper()
            pre_num = account.group('pre_num').replace(' ', '').upper()
            num = account.group('num').replace(' ', '').upper()

            if all([all([i in (LETTERS_UPPER + NUMBERS) for i in control_code]),
                    all([i in NUMBERS for i in bank_code]),
                    all([i in NUMBERS for i in pre_num]),
                    all([i in NUMBERS for i in num])]):
                return cls(
                    control_code=int(control_code), has_spaces=' ' in value,
                    pre_num=int(pre_num), num=int(num), bank=int(bank_code))

        raise ValidationError(f'IBAN \'{value}\' does not appear to be czech IBAN.')

    def _to_str(self, spaces: Optional[bool] = None):
        pre_num = str(self.pre_num or 0).rjust(6, '0')
        num = str(self.num).rjust(10, '0')
        out = (f'CZ{str(self.control_code).rjust(2, "0")} {str(self.bank).rjust(4, "0")} {pre_num[:4]} '
               f'{pre_num[4:]}{num[:2]} {num[2:6]} {num[6:]}')
        if (spaces is None and self.has_spaces) or spaces:
            return out
        return out.replace(' ', '')

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


class CzechPersonalID:
    date: datetime.date
    day_index: int
    control_number: Optional[int] = None

    day_offset: bool = False
    is_male: bool
    is_extra: bool = False
    has_slash: bool = True

    CZECH_PERSONAL_ID_RE = re.compile(
        r'^(?P<year>\d{2})(?P<month>\d{2})(?P<day>\d{2})/?(?P<day_index>\d{3})(?P<key>\d)?$')

    def __init__(self, date: datetime.date, is_male: bool, day_index: int, control_number: Optional[int] = None,
                 is_extra: bool = False, day_offset: bool = False, has_slash: bool = True):
        """

        Args:
            date: The ``datetime.date`` object of the Personal ID
            is_male: Is the person male? (Month + 50)
            day_index: The index of the person in the given day
            control_number: The last digit in personal id
            is_extra: Did we run out of IDs on that day? (Month + 20)
            day_offset: In some rare cases the days may be offset by 50 is this the case?
            has_slash: Show ``/`` in ``__str__`` representation

        """
        self.day_index = day_index
        self.date = date
        self.is_male = is_male
        self.control_number = control_number
        self.is_extra = is_extra
        self.day_offset = day_offset
        self.has_slash = has_slash

    @property
    def is_pre_1954(self):
        return self.date.year < 1954

    def __str__(self):
        month = self.date.month
        if not self.is_male:
            month += 50
        if self.is_extra:
            month += 20
        return (f'{str(self.date.year)[-2:]}{"%02d" % month}'
                f'{"%02d" % (self.date.day if not self.day_offset else self.date.day + 50)}'
                f'{"/" if self.has_slash else ""}{("%03d" % self.day_index)}'
                f'{self.control_number if self.control_number is not None else ""}')

    @classmethod
    def parse(cls, value) -> "CzechPersonalID":
        personal_id = re.match(cls.CZECH_PERSONAL_ID_RE, value)

        if personal_id is None:
            raise ValidationError(f'Str \'{value}\' does not appear to be czech personal id.')

        year = int(personal_id.group('year'))
        month = int(personal_id.group('month'))
        day = int(personal_id.group('day'))
        day_index = int(personal_id.group('day_index'))
        key = int(personal_id.group('key')) if personal_id.group('key') is not None else None

        pre_1954 = len(value.replace('/', '')) == 9
        is_male = month < 50
        is_extra = month > 12 if is_male else month > 62
        is_day_offset = day > 50
        full_year = (2000 if year < 54 and not pre_1954 else 1900) + year
        if is_male and is_extra and full_year > 2003:
            month -= 20
        elif not is_male and is_extra and full_year > 2003:
            month -= 70
        elif not is_male:
            month -= 50
        if not (1 <= month <= 12):
            raise ValidationError(f'Str \'{value}\' does not appear to be czech personal id.')

        if is_day_offset:
            day -= 50

        return cls(
            date=datetime.date(year=full_year, month=month, day=day),
            is_male=is_male,
            day_index=day_index,
            control_number=key,
            is_extra=is_extra,
            day_offset=is_day_offset,
            has_slash='/' in value,
        )

    def check_format(self):

        # Three digits for verification number were used until 1. january 1954
        if not self.is_pre_1954:
            """
            Fourth digit has been added since 1. January 1954.
            It is modulo of dividing birth number and verification number by 11.
            If the modulo were 10, the last number was 0 (and therefore, the whole
            birth number weren't dividable by 11. These number are no longer used (since 1985)
            and condition 'modulo == 10' can be removed some years after 2085.
            """

            modulo = int(str(self).replace('/', '')[:-1]) % 11

            if (modulo != self.control_number) and (modulo != 10 or self.control_number != 0):
                return False

        return True

    def brute_force_control_number(self):
        self.control_number = 0
        while not self.check_format():
            self.control_number += 1

    def encrypt(self, numeric_key):
        numeric_key %= 365

        if numeric_key % 2 == 0:
            self.is_male = not self.is_male

        self.date -= datetime.timedelta(days=numeric_key + 1)
        self.day_index = int(encrypt_text(str(numeric_key), str(self.day_index), NUMBERS))

        if self.is_pre_1954:
            self.control_number = None
        else:
            self.brute_force_control_number()

        return self  # Enable chaining

    def decrypt(self, numeric_key):
        numeric_key %= 365

        if numeric_key % 2 == 0:
            self.is_male = not self.is_male

        self.date += datetime.timedelta(days=numeric_key + 1)
        self.day_index = int(decrypt_text(str(numeric_key), str(self.day_index), NUMBERS))

        if self.is_pre_1954:
            self.control_number = None
        else:
            self.brute_force_control_number()

        return self  # Enable chaining


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

        account.num = int(encrypt_text(encryption_key, str(account.num), NUMBERS))

        return str(account)

    def get_decrypted_value(self, value: Any, encryption_key: str):
        account = CzechAccountNumber.parse(value)

        if self.use_smart_method and account.check_account_format():
            return str(account.brute_force_prev(self.get_numeric_encryption_key(encryption_key)))

        account.num = int(decrypt_text(encryption_key, str(account.num), NUMBERS))

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
        encrypted_phone_number = encrypt_text(encryption_key, phone_number[3:], NUMBERS)
        return f'{area_code}{phone_number[:3]}{encrypted_phone_number}'

    def get_decrypted_value(self, value: str, encryption_key: str):
        area_code, phone_number = self.split_phone_number(value)
        encrypted_phone_number = decrypt_text(encryption_key, phone_number[3:], NUMBERS)
        return f'{area_code}{phone_number[:3]}{encrypted_phone_number}'


class CzechIDCardFieldAnonymizer(NumericFieldAnonymizer):
    max_anonymization_range = int("9" * 9)

    def get_encrypted_value(self, value: str, encryption_key: str):
        return f"{value[0]}{encrypt_text(str(self.get_numeric_encryption_key(encryption_key)), value[1:], NUMBERS)}"

    def get_decrypted_value(self, value: str, encryption_key: str):
        return f"{value[0]}{decrypt_text(str(self.get_numeric_encryption_key(encryption_key)), value[1:], NUMBERS)}"


class CzechPersonalIDSmartFieldAnonymizer(NumericFieldAnonymizer):
    max_anonymization_range = 365

    def get_encrypted_value(self, value: str, encryption_key: str):
        return str(CzechPersonalID.parse(value).encrypt(self.get_numeric_encryption_key(encryption_key)))

    def get_decrypted_value(self, value: str, encryption_key: str):
        return str(CzechPersonalID.parse(value).decrypt(self.get_numeric_encryption_key(encryption_key)))
