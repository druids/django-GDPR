from decimal import Decimal

from django.test import TestCase

from faker import Faker
from gdpr.encryption import (
    decrypt_email_address, decrypt_text, encrypt_email_address, encrypt_text, translate_iban, translate_number
)
from germanium.tools import assert_equal, assert_not_equal


IBANS = [
    'AL47 2121 1009 0000 0002 3569 8741',
    'AD12 0001 2030 2003 5910 0100',
    'AZ21 NABZ 0000 0000 1370 1000 1944',
    'BH67 BMAG 0000 1299 1234 56',
    'BE68 5390 0754 7034',
    'BY13 NBRB 3600 9000 0000 2Z00 AB00',
    'BA39 1290 0794 0102 8494',
    'BR18 0036 0305 0000 1000 9795 493C 1',
    'VG96 VPVG 0000 0123 4567 8901',
    'BG80 BNBG 9661 1020 3456 78',
    'ME25 5050 0001 2345 6789 51',
    'CZ65 0800 0000 1920 0014 5399',
    'DK50 0040 0440 1162 43',
    'DO28 BAGR 0000 0001 2124 5361 1324',
    'EE38 2200 2210 2014 5685',
    'FI21 1234 5600 0007 85',
    'FR14 2004 1010 0505 0001 3M02 606',
    'GI75 NWBK 0000 0000 7099 453',
    'GE29 NB00 0000 0101 9049 17',
    'GT82 TRAJ 0102 0000 0012 1002 9690',
    'HR12 1001 0051 8630 0016 0',
    'IQ98 NBIQ 8501 2345 6789 012',
    'IE29 AIBK 9311 5212 3456 78',
    'IS14 0159 2600 7654 5510 7303 39',
    'IT60 X054 2811 1010 0000 0123 456',
    'IL62 0108 0000 0009 9999 999',
    'JO94 CBJO 0010 0000 0000 0131 0003 02',
    'QA58 DOHB 0000 1234 5678 90AB CDEF G',
    'KZ86 125K ZT50 0410 0100',
    'XK05 1212 0123 4567 8906',
    'CR05 0152 0200 1026 2840 66',
    'KW81 CBKU 0000 0000 0000 1234 5601 01',
    'CY17 0020 0128 0000 0012 0052 7600',
    'LB62 0999 0000 0001 0019 0122 9114',
    'LI21 0881 0000 2324 013A A',
    'LT12 1000 0111 0100 1000',
    'LV80 BANK 0000 4351 9500 1',
    'LU28 0019 4006 4475 0000',
    'HU42 1177 3016 1111 1018 0000 0000',
    'MK07 2501 2000 0058 984',
    'MT84 MALT 0110 0001 2345 MTLC AST0 01S',
    'MU17 BOMM 0101 1010 3030 0200 000M UR',
    'MR13 0002 0001 0100 0012 3456 753',
    'MD24 AG00 0225 1000 1310 4168',
    'MC58 1122 2000 0101 2345 6789 030',
    'DE89 3704 0044 0532 0130 00',
    'NL91 ABNA 0417 1643 00',
    'NO93 8601 1117 947',
    'PK36 SCBL 0000 0011 2345 6702',
    'PS92 PALS 0000 0000 0400 1234 5670 2',
    'PL61 1090 1014 0000 0712 1981 2874',
    'PT50 0002 0123 1234 5678 9015 4',
    'AT61 1904 3002 3457 3201',
    'RO49 AAAA 1B31 0075 9384 0000',
    'GR16 0110 1250 0000 0001 2300 695',
    'SV62 CENR 0000 0000 0000 0070 0025',
    'SM86 U032 2509 8000 0000 0270 100',
    'SA03 8000 0000 6080 1016 7519',
    'SC18 SSCB 1101 0000 0000 0000 1497 USD',
    'SK31 1200 0000 1987 4263 7541',
    'SI56 2633 0001 2039 086',
    'AE07 0331 2345 6789 0123 456',
    'RS35 2600 0560 1001 6113 79',
    'LC55 HEMM 0001 0001 0012 0012 0002 3015',
    'ST68 0001 0001 0051 8453 1011 2',
    'ES91 2100 0418 4502 0005 1332',
    'SE45 5000 0000 0583 9825 7466',
    'CH93 0076 2011 6238 5295 7',
    'TN59 1000 6035 1835 9847 8831',
    'TR33 0006 1005 1978 6457 8413 26',
    'UA21 3223 1300 0002 6007 2335 6600 1',
    'VA59 0011 2300 0012 3456 78',
    'GB29 NWBK 6016 1331 9268 19',
    'TL38 0080 0123 4567 8910 157',
]


class TestEncryption(TestCase):
    """
    Tests the `gdpr.encryption` module.
    """

    def setUp(self):
        self.faker = Faker()
        self.encryption_key = 'LoremIpsumDolorSitAmet'
        self.numeric_encryption_key = '314159265358'

    def test_encrypt_text_full_name(self):
        """
        Test function `gdpr.encryption.encrypt_text` by using human full name from Faker lib.
        """
        cleartext = self.faker.name()

        ciphertext = encrypt_text(self.encryption_key, cleartext)
        assert_not_equal(cleartext, ciphertext, "The encrypted name is equal to the original name.")

        decrypted = decrypt_text(self.encryption_key, ciphertext)
        assert_equal(cleartext, decrypted, "The decrypted name is not equal to the original name.")

    def test_encrypt_email_address(self):
        """
        Test function `gdpr.encryption.encrypt_email_address` by using email address from Faker lib.
        """
        cleartext = self.faker.email()

        ciphertext = encrypt_email_address(self.encryption_key, cleartext)
        assert_not_equal(cleartext, ciphertext, "The encrypted email address is equal to the original email address.")

        decrypted = decrypt_email_address(self.encryption_key, ciphertext)
        assert_equal(cleartext, decrypted, "The decrypted email address is not equal to the original email address.")

    def test_translate_iban(self):
        """
        Test function `gdpr.encryption.translate_iban` by using an example IBAN for every country using IBAN system.
        """
        for IBAN in IBANS:
            encrypted = translate_iban(self.encryption_key, IBAN)
            assert_not_equal(encrypted, IBAN, "The encrypted IBAN is equal to the original IBAN.")
            assert_equal(translate_iban(self.encryption_key, encrypted, False), IBAN,
                         "The decrypted IBAN is not equal to the original IBAN.")

    def test_translate_number_whole_positive(self):
        """
        Test metod `translate_number` on whole positive number.
        """
        number = 42
        encrypted = translate_number(self.numeric_encryption_key, number)

        assert_not_equal(number, encrypted)
        assert_equal(type(number), type(encrypted))

        decrypted = translate_number(self.numeric_encryption_key, encrypted, encrypt=False)

        assert_equal(number, decrypted)
        assert_equal(type(number), type(decrypted))

    def test_translate_number_whole_negative(self):
        """
        Test metod `translate_number` on whole negative number.
        """
        number = -42
        encrypted = translate_number(self.numeric_encryption_key, number)

        assert_not_equal(number, encrypted)
        assert_equal(type(number), type(encrypted))

        decrypted = translate_number(self.numeric_encryption_key, encrypted, encrypt=False)

        assert_equal(number, decrypted)
        assert_equal(type(number), type(decrypted))

    def test_translate_number_decimal_positive(self):
        """
        Test metod `translate_number` on decimal positive number.
        """
        number = Decimal("3.14")
        encrypted = translate_number(self.numeric_encryption_key, number)

        assert_not_equal(number, encrypted)
        assert_equal(type(number), type(encrypted))

        decrypted = translate_number(self.numeric_encryption_key, encrypted, encrypt=False)

        assert_equal(number, decrypted)
        assert_equal(type(number), type(decrypted))

    def test_translate_number_decimal_negative(self):
        """
        Test metod `translate_number` on decimal positive number.
        """
        number = Decimal("-3.14")
        encrypted = translate_number(self.numeric_encryption_key, number)

        assert_not_equal(number, encrypted)
        assert_equal(type(number), type(encrypted))

        decrypted = translate_number(self.numeric_encryption_key, encrypted, encrypt=False)

        assert_equal(number, decrypted)
        assert_equal(type(number), type(decrypted))
