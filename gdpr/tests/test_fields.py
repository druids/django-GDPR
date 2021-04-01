import json
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from gdpr.anonymizers import (
    CharFieldAnonymizer, DateFieldAnonymizer, DecimalFieldAnonymizer, EmailFieldAnonymizer, IPAddressFieldAnonymizer,
    StaticValueFieldAnonymizer
)
from gdpr.anonymizers.fields import (
    DateTimeFieldAnonymizer, FunctionFieldAnonymizer, IntegerFieldAnonymizer, JSONFieldAnonymizer,
    SiteIDUsernameFieldAnonymizer
)
from germanium.tools import assert_dict_equal, assert_equal, assert_list_equal, assert_not_equal


class TestCharField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = CharFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_char_field(self):
        name = 'John CENA'
        out = self.field.get_encrypted_value(name, self.encryption_key)

        assert_not_equal(out, name)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, name)

    def test_char_field_transliteration(self):
        name = 'François'
        fixed_name = 'Francois'
        field = CharFieldAnonymizer(transliterate=True)
        out = field.get_encrypted_value(name, self.encryption_key)

        assert_not_equal(out, name)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, fixed_name)

    def test_char_field_transliteration_full_czech(self):
        text = 'Příliš žluťoučký kůň úpěl ďábelské ódy'
        fixed_text = 'Prilis zlutoucky kun upel dabelske ody'
        field = CharFieldAnonymizer(transliterate=True)
        out = field.get_encrypted_value(text, self.encryption_key)

        assert_not_equal(out, text)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, fixed_text)


class TestEmailField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = EmailFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_email_field(self):
        email = 'foo@bar.com'
        out = self.field.get_encrypted_value(email, self.encryption_key)

        assert_not_equal(out, email)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, email)


class TestSiteIDUsernameFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = SiteIDUsernameFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_just_email(self):
        email = 'foo@bar.com'
        out = self.field.get_encrypted_value(email, self.encryption_key)

        assert_not_equal(out, email)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, email)

    def test_normal(self):
        email = '1:foo@bar.com'
        out = self.field.get_encrypted_value(email, self.encryption_key)

        assert_not_equal(out, email)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, email)


class TestDateField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DateFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_date_field(self):
        date = timezone.now()
        out = self.field.get_encrypted_value(date, self.encryption_key)

        assert_not_equal(out, date)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, date)


class TestDateTimeField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DateTimeFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_date_field(self):
        date = timezone.now()
        out = self.field.get_encrypted_value(date, self.encryption_key)

        assert_not_equal(out, date)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, date)


class TestDecimalField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = DecimalFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_decimal_field_positive(self):
        decimal = Decimal('3.14159265358979')
        out = self.field.get_encrypted_value(decimal, self.encryption_key)

        assert_not_equal(out, decimal)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, decimal)

    def test_decimal_field_negative(self):
        decimal = Decimal('-3.14159265358979')
        out = self.field.get_encrypted_value(decimal, self.encryption_key)

        assert_not_equal(out, decimal)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, decimal)


class TestIntegerField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = IntegerFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_integer_field_positive(self):
        number = 42
        out = self.field.get_encrypted_value(number, self.encryption_key)

        assert_not_equal(out, number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, number)

    def test_integer_field_negative(self):
        number = -42
        out = self.field.get_encrypted_value(number, self.encryption_key)

        assert_not_equal(out, number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, number)


class TestIPAddressField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = IPAddressFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_ip_addr_v_4_field(self):
        ip = '127.0.0.1'
        out = self.field.get_encrypted_value(ip, self.encryption_key)

        assert_not_equal(out, ip)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, ip)

    def test_ip_addr_v_6_field(self):
        ip = '::1'
        out = self.field.get_encrypted_value(ip, self.encryption_key)

        assert_not_equal(out, ip)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, ip)


class TestStaticValueAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = StaticValueFieldAnonymizer('U_SHALL_NOT_PASS')
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_static_field(self):
        text = 'ORANGE'
        out = self.field.get_encrypted_value(text, self.encryption_key)

        assert_not_equal(out, text)


class TestFunctionField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_one_way_function_field(self):
        number = 5
        self.field = FunctionFieldAnonymizer(lambda x, key: x ** 2)
        out = self.field.get_encrypted_value(number, self.encryption_key)

        assert_not_equal(out, number)

    def test_two_way_function_field(self):
        number = 5
        self.field = FunctionFieldAnonymizer(lambda a, x, key: x + a.get_numeric_encryption_key(key),
                                             lambda a, x, key: x - a.get_numeric_encryption_key(key))
        self.field.max_anonymization_range = 100
        out = self.field.get_encrypted_value(number, self.encryption_key)

        assert_not_equal(out, number)

        out_decrypt = self.field.get_decrypted_value(out, self.encryption_key)

        assert_equal(out_decrypt, number)


class TestJSONFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = JSONFieldAnonymizer()
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    def test_str_value(self):
        text = 'John CENA'
        out = self.field.anonymize_json_value(text, self.encryption_key)

        assert_not_equal(out, text)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        assert_equal(out_decrypt, text)

    def test_none_value(self):
        value = None
        out = self.field.anonymize_json_value(value, self.encryption_key)

        assert_equal(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        assert_equal(out_decrypt, value)

    def test_int_value(self):
        value = 158
        out = self.field.anonymize_json_value(value, self.encryption_key)

        assert_not_equal(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        assert_equal(out_decrypt, value)

    def test_int_value_overflow(self):
        value = 9
        out = self.field.anonymize_json_value(value, self.encryption_key)

        assert_not_equal(out, value)
        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        assert_equal(out_decrypt, value)

    def test_dict(self):
        json_dict = {
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

        out = self.field.anonymize_json_value(json_dict, self.encryption_key)

        assert_not_equal(out, json_dict)

        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        assert_dict_equal(json_dict, out_decrypt)

    def test_dict_str(self):
        json_dict = {
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

        out = json.loads(self.field.get_encrypted_value(json.dumps(json_dict), self.encryption_key))

        assert_not_equal(out, json_dict)

        out_decrypt = json.loads(self.field.get_decrypted_value(json.dumps(out), self.encryption_key))

        assert_dict_equal(json_dict, out_decrypt)

    def test_list(self):
        json_list = ['banana', 'oranges', 5, 3.14, False, None, {'name': 'Bob'}]

        out = self.field.anonymize_json_value(json_list, self.encryption_key)

        assert_not_equal(out, json_list)

        out_decrypt = self.field.anonymize_json_value(out, self.encryption_key, False)

        assert_list_equal(json_list, out_decrypt)

    def test_list_str(self):
        json_list = ['banana', 'oranges', 5, 3.14, False, None, {'name': 'Bob'}]

        out = json.loads(self.field.get_encrypted_value(json.dumps(json_list), self.encryption_key))

        assert_not_equal(out, json_list)

        out_decrypt = json.loads(self.field.get_decrypted_value(json.dumps(out), self.encryption_key))

        assert_list_equal(json_list, out_decrypt)
