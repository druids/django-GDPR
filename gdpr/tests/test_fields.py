from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from gdpr.anonymizers import (
    CharFieldAnonymizer, DateFieldAnonymizer, DecimalFieldAnonymizer,
    EmailFieldAnonymizer, IPAddressFieldAnonymizer, StaticValueAnonymizer
)
from gdpr.anonymizers.fields import FunctionFieldAnonymizer, JSONFieldAnonymizer, SiteIDUsernameFieldAnonymizer


class TestCharField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CharFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_char_field(self):
        name = 'John CENA'
        out = self.field.get_encrypted_value(name, self.encryption_key)

        self.assertNotEqual(out, name)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, name)


class TestEmailField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = EmailFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_email_field(self):
        email = 'foo@bar.com'
        out = self.field.get_encrypted_value(email, self.encryption_key)

        self.assertNotEqual(out, email)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, email)


class TestSiteIDUsernameFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = SiteIDUsernameFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_just_email(self):
        email = 'foo@bar.com'
        out = self.field.get_encrypted_value(email, self.encryption_key)

        self.assertNotEqual(out, email)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, email)

    def test_normal(self):
        email = '1:foo@bar.com'
        out = self.field.get_encrypted_value(email, self.encryption_key)

        self.assertNotEqual(out, email)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, email)


class TestDateField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DateFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_date_field(self):
        date = timezone.now()
        out = self.field.get_encrypted_value(date, self.encryption_key)

        self.assertNotEqual(out, date)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, date)


class TestDecimalField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DecimalFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_decimal_field(self):
        decimal = Decimal('3.14159265358979')
        out = self.field.get_encrypted_value(decimal, self.encryption_key)

        self.assertNotEqual(out, decimal)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, decimal)


class TestIPAddressField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = IPAddressFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_ip_addr_v_4_field(self):
        ip = '127.0.0.1'
        out = self.field.get_encrypted_value(ip, self.encryption_key)

        self.assertNotEqual(out, ip)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, ip)

    def test_ip_addr_v_6_field(self):
        ip = '::1'
        out = self.field.get_encrypted_value(ip, self.encryption_key)

        self.assertNotEqual(out, ip)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, ip)


class TestStaticValueAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = StaticValueAnonymizer('U_SHALL_NOT_PASS')
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_static_field(self):
        text = 'ORANGE'
        out = self.field.get_encrypted_value(text, self.encryption_key)

        self.assertNotEqual(out, text)


class TestFunctionField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_one_way_function_field(self):
        number = 5
        self.field = FunctionFieldAnonymizer(lambda x, key: x ** 2)
        out = self.field.get_encrypted_value(number, self.encryption_key)

        self.assertNotEqual(out, number)

    def test_two_way_function_field(self):
        number = 5
        self.field = FunctionFieldAnonymizer(lambda a, x, key: x + a.get_numeric_encryption_key(key),
                                             lambda a, x, key: x - a.get_numeric_encryption_key(key))
        self.field.max_anonymization_range = 100
        out = self.field.get_encrypted_value(number, self.encryption_key)

        self.assertNotEqual(out, number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        self.assertEqual(out_decrypt, number)


class TestJSONFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = JSONFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_str_value(self):
        text = 'John CENA'
        out = self.field.anonymize_json_value(text, self.encryption_key)

        self.assertNotEqual(out, text)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertEqual(out_decrypt, text)

    def test_none_value(self):
        value = None
        out = self.field.anonymize_json_value(value, self.encryption_key)

        self.assertEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertEqual(out_decrypt, value)

    def test_int_value(self):
        value = 158
        out = self.field.anonymize_json_value(value, self.encryption_key)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertEqual(out_decrypt, value)

    def test_int_value_overflow(self):
        value = 9
        out = self.field.anonymize_json_value(value, self.encryption_key)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertEqual(out_decrypt, value)

    def test_float_value(self):
        value = 3.14
        out = self.field.anonymize_json_value(value, self.encryption_key)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertEqual(out_decrypt, value)

    def test_float_value_overflow(self):
        value = 9.14
        out = self.field.anonymize_json_value(value, self.encryption_key)

        self.assertNotEqual(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertEqual(out_decrypt, value)

    def test_dict(self):
        json = {
            'breed': 'labrador',
            'owner': {
                'name': 'Bob',
                'other_pets': [{'name': 'Fishy'}]
            },
            'age': 5,
            'height': 9.5,
            'is_brown': True,
            'none_field': None
        }

        out = self.field.anonymize_json_value(json, self.encryption_key)

        self.assertTrue(out != json)

        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertDictEqual(json, out_decrypt)

    def test_list(self):
        json = ["banana", "oranges", 5, 3.14, False, None, {'name': 'Bob'}]

        out = self.field.anonymize_json_value(json, self.encryption_key)

        self.assertTrue(out != json)

        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        self.assertListEqual(json, out_decrypt)
