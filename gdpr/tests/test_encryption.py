from django.test import TestCase
from faker import Faker

from gdpr.encryption import (
    encrypt_message, decrypt_message, encrypt_email,
    decrypt_email)


class TestEncryption(TestCase):
    def setUp(self):
        self.faker = Faker()
        self.encryption_key = "LoremIpsumDolorSitAmet"

    def test_basic_name_encryption(self):
        cleartext = self.faker.name()
        ciphertext = encrypt_message(self.encryption_key, cleartext)

        self.assertNotEqual(cleartext, ciphertext)

        decrypted = decrypt_message(self.encryption_key, ciphertext)

        self.assertEqual(cleartext, decrypted)

    def test_email_encryption(self):
        cleartext = self.faker.email()
        ciphertext = encrypt_email(self.encryption_key, cleartext)

        self.assertNotEqual(cleartext, ciphertext)

        decrypted = decrypt_email(self.encryption_key, ciphertext)

        self.assertEqual(cleartext, decrypted)
