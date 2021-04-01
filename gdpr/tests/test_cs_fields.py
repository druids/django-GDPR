from django.core.exceptions import ValidationError
from django.test import TestCase

from gdpr.anonymizers.local.cs import (
    CzechAccountNumber, CzechAccountNumberFieldAnonymizer, CzechIBAN, CzechIBANSmartFieldAnonymizer,
    CzechIDCardFieldAnonymizer, CzechPersonalIDSmartFieldAnonymizer, CzechPhoneNumberFieldAnonymizer
)
from germanium.tools import assert_equal, assert_false, assert_not_equal, assert_raises, assert_true


class TestCzechAccountNumberField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechAccountNumberFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_account_number_simple_field(self):
        account_number = '2501277007/2010'
        out = self.field.get_encrypted_value(account_number, self.encryption_key)

        assert_not_equal(out, account_number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, account_number)

    def test_account_number_simple_field_smart_method(self):
        field = CzechAccountNumberFieldAnonymizer(use_smart_method=True)
        account_number = '2501277007/2010'
        out = field.get_encrypted_value(account_number, self.encryption_key)

        assert_not_equal(out, account_number)

        out_decrypt = field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, account_number)

    def test_account_number_with_pre_num_field(self):
        account_number = '19-2000145399/0800'
        out = self.field.get_encrypted_value(account_number, self.encryption_key)

        assert_not_equal(out, account_number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, account_number)

    def test_account_number_with_pre_num_field_smart_method(self):
        field = CzechAccountNumberFieldAnonymizer(use_smart_method=True)
        account_number = '19-2000145399/0800'
        out = field.get_encrypted_value(account_number, self.encryption_key)

        assert_not_equal(out, account_number)

        out_decrypt = field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, account_number)

    def test_account_format_check(self):
        assert_true(CzechAccountNumber.parse('19-2000145399/0800').check_account_format())
        assert_true(CzechAccountNumber.parse('2501277007/2010').check_account_format())

    def test_brute_force(self):
        account = CzechAccountNumber.parse('19-2000145399/0800')
        key = 314
        original_account_num = account.num

        account.brute_force_next(key)

        assert_not_equal(original_account_num, account.num)

        account.brute_force_prev(key)

        assert_equal(original_account_num, account.num)


class TestCzechIBANSmartFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechIBANSmartFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'
        cls.text_iban = 'CZ65 0800 0000 1920 0014 5399'
        cls.no_space_text_iban = 'CZ6508000000192000145399'
        cls.invalid_text_iban = 'CZ00 0800 0000 1920 0014 5399'
        cls.no_pre_num_iban = 'CZ4601000000000099550247'

    def test_czech_iban_field(self):
        out = self.field.get_encrypted_value(self.text_iban, self.encryption_key)
        assert_not_equal(out, self.text_iban)

        out_decrypted = self.field.get_decrypted_value(out, self.encryption_key)
        assert_equal(out_decrypted, self.text_iban)

    def test_czech_iban_field_no_space(self):
        out = self.field.get_encrypted_value(self.no_space_text_iban, self.encryption_key)
        assert_not_equal(out, self.no_space_text_iban)
        assert_not_equal(out, self.text_iban)

        out_decrypted = self.field.get_decrypted_value(out, self.encryption_key)
        assert_equal(out_decrypted, self.no_space_text_iban)

    def test_czech_iban_field_get_encrypted_value_invalid_format_raises(self):
        assert_raises(ValidationError, self.field.get_encrypted_value, self.invalid_text_iban, self.encryption_key)

    def test_czech_iban_field_get_decrypted_value_invalid_format_raises(self):
        assert_raises(ValidationError, self.field.get_decrypted_value, self.invalid_text_iban, self.encryption_key)

    def test_czech_iban_parse_and_str_with_spaces(self):
        assert_equal(self.text_iban, str(CzechIBAN.parse(self.text_iban)))

    def test_czech_iban_parse_and_str_without_spaces(self):
        assert_equal(self.no_space_text_iban, str(CzechIBAN.parse(self.no_space_text_iban)))

    def test_czech_iban_check_format(self):
        assert_true(CzechIBAN.parse(self.text_iban).check_iban_format())

    def test_czech_iban_check_format_invalid(self):
        assert_false(CzechIBAN.parse(self.invalid_text_iban).check_iban_format())

    def test_czech_iban_check_format_no_pre_num(self):
        assert_true(CzechIBAN.parse(self.no_pre_num_iban).check_iban_format())

    def test_brute_force(self):
        account = CzechIBAN.parse(self.text_iban)
        key = 314

        account.brute_force_next(key)
        assert_not_equal(self.text_iban, str(account))

        account.brute_force_prev(key)
        assert_equal(self.text_iban, str(account))


class TestCzechPhoneNumberField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechPhoneNumberFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_basic_phone_number(self):
        phone_number = '608104120'
        out = self.field.get_encrypted_value(phone_number, self.encryption_key)

        assert_not_equal(phone_number, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(phone_number, out_decrypt)

    def test_plus_area_code_phone_number(self):
        phone_number = '+420608104120'
        out = self.field.get_encrypted_value(phone_number, self.encryption_key)

        assert_not_equal(phone_number, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(phone_number, out_decrypt)

    def test_zero_zero_area_code_phone_number(self):
        phone_number = '+420608104120'
        out = self.field.get_encrypted_value(phone_number, self.encryption_key)

        assert_not_equal(phone_number, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(phone_number, out_decrypt)


class TestCzechIDCardFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechIDCardFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_czech_id_card_field_anonymizer(self):
        id_card = "297065518"

        out = self.field.get_encrypted_value(id_card, self.encryption_key)
        assert_not_equal(id_card, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)
        assert_equal(id_card, out_decrypt)


class TestCzechPersonalIDSmartFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechPersonalIDSmartFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_czech_personal_id_smart_field_anonymizer(self):
        personal_id = "740104/0020"

        out = self.field.get_encrypted_value(personal_id, self.encryption_key)
        assert_not_equal(personal_id, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)
        assert_equal(personal_id, out_decrypt)

    def test_czech_personal_id_smart_field_anonymizer_no_slash(self):
        personal_id = "7401040020"

        out = self.field.get_encrypted_value(personal_id, self.encryption_key)
        assert_not_equal(personal_id, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)
        assert_equal(personal_id, out_decrypt)

    def test_czech_personal_id_smart_field_anonymizer_1954_change(self):
        personal_id = "540101/0021"

        out = self.field.get_encrypted_value(personal_id, self.encryption_key)
        assert_not_equal(personal_id, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)
        assert_equal(personal_id, out_decrypt)
