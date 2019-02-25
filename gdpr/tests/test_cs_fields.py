from django.test import TestCase

from gdpr.anonymizers.local.cs import CzechAccountNumberFieldAnonymizer, CzechPhoneNumberAnonymizer


class TestCzechAccountNumberField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechAccountNumberFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_account_number_simple_field(self):
        account_number = '2501277007/2010'
        out = self.field.get_encrypted_value(account_number, self.encryption_key)

        self.assertNotEqual(out, account_number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, account_number)

    def test_account_number_simple_field_smart_method(self):
        field = CzechAccountNumberFieldAnonymizer(use_smart_method=True)
        account_number = '2501277007/2010'
        out = field.get_encrypted_value(account_number, self.encryption_key)

        self.assertNotEqual(out, account_number)

        out_decrypt = field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, account_number)

    def test_account_number_with_pre_num_field(self):
        account_number = '19-2000145399/0800'
        out = self.field.get_encrypted_value(account_number, self.encryption_key)

        self.assertNotEqual(out, account_number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, account_number)

    def test_account_number_with_pre_num_field_smart_method(self):
        field = CzechAccountNumberFieldAnonymizer(use_smart_method=True)
        account_number = '19-2000145399/0800'
        out = field.get_encrypted_value(account_number, self.encryption_key)

        self.assertNotEqual(out, account_number)

        out_decrypt = field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, account_number)

    def test_account_format_check(self):
        self.assertTrue(self.field.check_account_format(self.field.parse_value('19-2000145399/0800')))
        self.assertTrue(self.field.check_account_format(self.field.parse_value('2501277007/2010')))

    def test_brute_force(self):
        account = self.field.parse_value('19-2000145399/0800')
        key = 314

        out = self.field.brute_force_next(account, key)

        self.assertNotEqual(account.num, out.num)

        out_decrypt = self.field.brute_force_prev(out, key)

        self.assertEqual(account.num, out_decrypt.num)


class TestCzechPhoneNumberField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechPhoneNumberAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_basic_phone_number(self):
        phone_number = "608104120"
        out = self.field.get_encrypted_value(phone_number, self.encryption_key)

        self.assertNotEqual(phone_number, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(phone_number, out_decrypt)

    def test_plus_area_code_phone_number(self):
        phone_number = "+420608104120"
        out = self.field.get_encrypted_value(phone_number, self.encryption_key)

        self.assertNotEqual(phone_number, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(phone_number, out_decrypt)

    def test_zero_zero_area_code_phone_number(self):
        phone_number = "+420608104120"
        out = self.field.get_encrypted_value(phone_number, self.encryption_key)

        self.assertNotEqual(phone_number, out)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(phone_number, out_decrypt)
