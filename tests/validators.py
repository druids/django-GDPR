import re
from datetime import date

from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _


def get_day_from_personal_id(personal_id):
    day = int(personal_id[4:6])
    if day > 50:
        day -= 50
    return day


def get_month_from_personal_id(personal_id):
    year = get_year_from_personal_id(personal_id)
    month = int(personal_id[2:4])
    if month > 70 and year > 2003:
        month -= 70
    elif month > 50:
        month -= 50
    elif month > 20 and year > 2003:
        month -= 20
    return month


def get_year_from_personal_id(personal_id):
    year = int(personal_id[0:2])
    value = personal_id.replace('/', '')
    year += 2000 if year < 54 and len(value) == 10 else 1900
    return year


def personal_id_date(personal_id):
    try:
        return date(get_year_from_personal_id(personal_id), get_month_from_personal_id(personal_id),
                    get_day_from_personal_id(personal_id))
    except ValueError:
        raise ValueError('Invalid personal id')


class CZBirthNumberValidator:
    """
    Czech birth number field validator.
    """
    BIRTH_NUMBER = re.compile(r'^(?P<birth>\d{6})/?(?P<id>\d{3,4})$')

    def __call__(self, value):
        value = force_text(value)

        match = re.match(self.BIRTH_NUMBER, value)
        if not match:
            raise ValidationError(_('Enter a birth number in the format XXXXXX/XXXX.'))

        birth, id = match.groupdict()['birth'], match.groupdict()['id']

        # Three digits for verificatin number were used until 1. january 1954
        if len(id) != 3:
            # Fourth digit has been added since 1. January 1954.
            # It is modulo of dividing birth number and verification number by 11.
            # If the modulo were 10, the last number was 0 (and therefore, the whole
            # birth number weren't dividable by 11. These number are no longer used (since 1985)
            # and condition 'modulo == 10' can be removed in 2085.

            modulo = int(birth + id[:3]) % 11

            if (modulo != int(id[-1])) and (modulo != 10 or id[-1] != '0'):
                raise ValidationError(_('Enter a valid birth number.'))

        try:
            personal_id_date(value)
        except ValueError:
            raise ValidationError(_('Enter a valid birth number.'))


class IDCardNoValidator:
    """
    Czech id card number field validator.
    """
    ID_CARD_NUMBER = re.compile(r'^\d{9}$')

    def __call__(self, value):
        value = force_text(value)

        match = re.match(self.ID_CARD_NUMBER, value)
        if not match:
            raise ValidationError(_('Enter an ID card in the format XXXXXXXXX.'))
        elif value[0] == '0':
            raise ValidationError(_('Enter a valid ID card number.'))
        else:
            return value


class BankAccountValidator:
    BANK_ACCOUNT_NUMBER_REVERSE_PATTERN = re.compile(
        r'^(?P<bank>\d{1,6})/(?P<number>\d{1,10})(-?(?P<prefix>\d{1,6}))?$')

    def __call__(self, value):
        match = re.match(self.BANK_ACCOUNT_NUMBER_REVERSE_PATTERN, force_text(value)[::-1])
        if match:
            return construct_bank_account_number((match.groupdict()['prefix'] or '')[::-1],
                                                 match.groupdict()['number'][::-1],
                                                 match.groupdict()['bank'][::-1])
        else:
            raise ValidationError(_('Enter a valid bank account number.'))


def construct_bank_account_number(prefix, number, bank_code):
    return '{:0>6}-{:0>10}/{}'.format(prefix, number, bank_code)


def split_bank_account_to_prefix_postfix(bank_account_number):
    return bank_account_number.split('-') if '-' in bank_account_number else ('', bank_account_number)


def clean_bank_account_number_or_none(bank_account_number):
    try:
        return BankAccountValidator()(bank_account_number)
    except ValidationError:
        return None
