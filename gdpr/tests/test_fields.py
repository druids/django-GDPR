from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from gdpr.anonymizers import (
    CharFieldAnonymizer, EmailFieldAnonymizer, DateFieldAnonymizer, DecimalFieldAnonymizer,
    IPAddressFieldAnonymizer, CzechAccountNumberFieldAnonymizer, StaticValueAnonymizer)
from gdpr.anonymizers.fields import FunctionFieldAnonymizer, JSONFieldAnonymizer


class TestCharField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CharFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_char_field(self):
        name = 'John CENA'
        out = self.field.get_encrypted_value(name)

        self.assertNotEqual(out, name)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, name)


class TestEmailField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = EmailFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_email_field(self):
        email = 'foo@bar.com'
        out = self.field.get_encrypted_value(email)

        self.assertNotEqual(out, email)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, email)


class TestDateField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DateFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_date_field(self):
        date = timezone.now()
        out = self.field.get_encrypted_value(date)

        self.assertNotEqual(out, date)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, date)


class TestDecimalField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DecimalFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_decimal_field(self):
        decimal = Decimal('3.14159265358979')
        out = self.field.get_encrypted_value(decimal)

        self.assertNotEqual(out, decimal)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, decimal)


class TestIPAddressField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = IPAddressFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_ip_addr_v_4_field(self):
        ip = '127.0.0.1'
        out = self.field.get_encrypted_value(ip)

        self.assertNotEqual(out, ip)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, ip)

    def test_ip_addr_v_6_field(self):
        ip = '::1'
        out = self.field.get_encrypted_value(ip)

        self.assertNotEqual(out, ip)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, ip)


class TestAccountNumberField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CzechAccountNumberFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_account_number_simple_field(self):
        account_number = '2501277007/2010'
        out = self.field.get_encrypted_value(account_number)

        self.assertNotEqual(out, account_number)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, account_number)

    def test_account_number_with_pre_num_field(self):
        account_number = '19-2000145399/0800'
        out = self.field.get_encrypted_value(account_number)

        self.assertNotEqual(out, account_number)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, account_number)


class TestStaticValueAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = StaticValueAnonymizer('U_SHALL_NOT_PASS')
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_static_field(self):
        text = 'ORANGE'
        out = self.field.get_anonymized_value(text)

        self.assertNotEqual(out, text)


class TestFunctionField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_one_way_function_field(self):
        number = 5
        self.field = FunctionFieldAnonymizer(lambda x: x ** 2)
        out = self.field.get_encrypted_value(number)

        self.assertNotEqual(out, number)

    def test_two_way_function_field(self):
        number = 5
        self.field = FunctionFieldAnonymizer(lambda a, x: x + a.get_numeric_encryption_key(),
                                             lambda a, x: x - a.get_numeric_encryption_key())
        self.field.max_anonymization_range = 100
        self.field._encryption_key = self._encryption_key
        out = self.field.get_encrypted_value(number)

        self.assertNotEqual(out, number)

        out_decrypt = self.field.get_decrypted_value(out)

        self.assertEqual(out_decrypt, number)


class TestJSONFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = JSONFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_str_value(self):
        text = 'John CENA'
        out = self.field.anonymize_json_value(text)

        self.assertNotEqual(out, text)
        out_decrypt = self.field.anonymize_json_value(out, False)

        self.assertEqual(out_decrypt, text)

    def test_none_value(self):
        value = None
        out = self.field.anonymize_json_value(value)

        self.assertEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, False)

        self.assertEqual(out_decrypt, value)

    def test_int_value(self):
        value = 158
        out = self.field.anonymize_json_value(value)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, False)

        self.assertEqual(out_decrypt, value)

    def test_int_value_overflow(self):
        value = 9
        out = self.field.anonymize_json_value(value)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, False)

        self.assertEqual(out_decrypt, value)

    def test_float_value(self):
        value = 3.14
        out = self.field.anonymize_json_value(value)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, False)

        self.assertEqual(out_decrypt, value)

    def test_float_value_overflow(self):
        value = 9.14
        out = self.field.anonymize_json_value(value)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, False)

        self.assertEqual(out_decrypt, value)

    def test_dict(self):
        json = {
            'breed': 'labrador',
            'owner': {
                'name': 'Bob',
                'other_pets': [{'name': 'Fishy'}]},
            'age': 5,
            'height': 9.5,
            'is_brown': True,
            'none_field': None
        }

        out = self.field.anonymize_json(json)

        self.assertTrue(out != json)

        out_decrypt = self.field.anonymize_json(out, False)

        self.assertDictEqual(json, out_decrypt)

    def test_list(self):
        json = ["banana", "oranges", 5, 3.14, False, None, {'name': 'Bob'}]

        out = self.field.anonymize_json(json)

        self.assertTrue(out != json)

        out_decrypt = self.field.anonymize_json(out, False)

        self.assertListEqual(json, out_decrypt)
