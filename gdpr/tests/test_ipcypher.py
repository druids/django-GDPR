from django.test import TestCase

from gdpr.ipcypher import decrypt_ip, decrypt_ipv4, decrypt_ipv6, derive_key, encrypt_ip, encrypt_ipv4, encrypt_ipv6
from germanium.tools import assert_equal


KEY_EMPTY_CLEAR = ''
KEY_EMPTY = bytearray.fromhex('bb8dcd7be9a6f43b3304c640d7d7103c')

KEY_PI_CLEAR = '3.141592653589793'
KEY_PI = bytearray.fromhex('3705bd6c0e26a1a839898f1fa016a374')

KEY_CRYPTO_CLEAR = 'crypto is not a coin'
KEY_CRYPTO = bytearray.fromhex('06c4bad23a38b9e0ad9d0590b0a3d93a')

KEY = 'crypto is not a coin'


class TestIPCrypt(TestCase):
    def test_derivation_empty(self):
        key = derive_key(KEY_EMPTY_CLEAR)

        assert_equal(KEY_EMPTY, key)

    def test_derivation_pi(self):
        key = derive_key(KEY_PI_CLEAR)

        assert_equal(KEY_PI, key)

    def test_derivation_crypto(self):
        key = derive_key(KEY_CRYPTO_CLEAR)

        assert_equal(KEY_CRYPTO, key)

    def test_ipv4_key_1(self):
        clear_ip = '198.41.0.4'
        encrypted_ip = encrypt_ipv4(KEY, clear_ip)
        decrypted_ip = decrypt_ipv4(KEY, encrypted_ip)

        assert_equal(encrypted_ip, '139.111.117.167')
        assert_equal(decrypted_ip, clear_ip)

    def test_ipv4_key_2(self):
        clear_ip = '130.161.180.1'
        encrypted_ip = encrypt_ipv4(KEY, clear_ip)
        decrypted_ip = decrypt_ipv4(KEY, encrypted_ip)

        assert_equal(encrypted_ip, '66.235.221.231')
        assert_equal(decrypted_ip, clear_ip)

    def test_ipv4_key_3(self):
        clear_ip = '0.0.0.0'
        encrypted_ip = encrypt_ipv4(KEY, clear_ip)
        decrypted_ip = decrypt_ipv4(KEY, encrypted_ip)

        assert_equal(encrypted_ip, '203.253.152.187')
        assert_equal(decrypted_ip, clear_ip)

    def test_ipv6_key_1(self):
        clear_ip = '::1'
        encrypted_ip = encrypt_ipv6(KEY, clear_ip)
        decrypted_ip = decrypt_ipv6(KEY, encrypted_ip)

        assert_equal(encrypted_ip, 'a551:9cb0:c9b:f6e1:6112:58a:af29:3a6c')
        assert_equal(decrypted_ip, clear_ip)

    def test_ipv6_key_2(self):
        clear_ip = '2001:503:ba3e::2:30'
        encrypted_ip = encrypt_ipv6(KEY, clear_ip)
        decrypted_ip = decrypt_ipv6(KEY, encrypted_ip)

        assert_equal(encrypted_ip, '6e60:2674:2fac:d383:f9d5:dcfe:fc53:328e')
        assert_equal(decrypted_ip, clear_ip)

    def test_ipv6_key_3(self):
        clear_ip = '2001:db8::'
        encrypted_ip = encrypt_ipv6(KEY, clear_ip)
        decrypted_ip = decrypt_ipv6(KEY, encrypted_ip)

        assert_equal(encrypted_ip, 'a8f5:16c8:e2ea:23b9:748d:67a2:4107:9d2e')
        assert_equal(decrypted_ip, clear_ip)

    def test_general_function_ipv4(self):
        clear_ip = '198.41.0.4'
        encrypted_ip = encrypt_ip(KEY, clear_ip)
        decrypted_ip = decrypt_ip(KEY, encrypted_ip)

        assert_equal(encrypted_ip, '139.111.117.167')
        assert_equal(decrypted_ip, clear_ip)

    def test_general_function_ipv6(self):
        clear_ip = '::1'
        encrypted_ip = encrypt_ip(KEY, clear_ip)
        decrypted_ip = decrypt_ip(KEY, encrypted_ip)

        assert_equal(encrypted_ip, 'a551:9cb0:c9b:f6e1:6112:58a:af29:3a6c')
        assert_equal(decrypted_ip, clear_ip)
