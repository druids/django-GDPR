from itertools import repeat, cycle

from django.utils.translation import gettext as _

__all__ = ["encrypt_message", "decrypt_message", "encrypt_email", "decrypt_email", "numerize_key"]

# Vigenere like Cipher (Polyalphabetic Substitution Cipher)

# Translators: Add special characters of your language at the end
NUMBERS = "1234567890"
LETTERS_ONLY = "abcdefghijklmnopqrstuvwxyz"
LETTERS_UPPER = LETTERS_ONLY.upper()
SYMBOLS = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
LETTERS = _(" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
# https://en.wikipedia.org/wiki/Email_address#Local-part
EMAIL_LOCAL_LETTERS = "!#$%&'*+-/0123456789=?ABCDEFGHIJKLMNOPQRSTUVWXYZ^_`abcdefghijklmnopqrstuvwxyz{|}~"
DOMAIN_LETTERS = LETTERS_ONLY + NUMBERS  # RFC952 + RFC1123


def translate_message(key: str, message: str, encrypt: bool = True, letters: str = LETTERS) -> str:
    translated = []

    key_index = 0
    for symbol in message:
        num = letters.find(symbol)
        if num != -1:
            num += (1 if encrypt else -1) * letters.find(key[key_index])
            num %= len(letters)

            translated.append(letters[num])

            key_index += 1
            if key_index == len(key):
                key_index = 0
        else:
            translated.append(symbol)

    return "".join(translated)


def encrypt_message(key: str, message: str, letters: str = LETTERS) -> str:
    return translate_message(key, message, True, letters)


def decrypt_message(key: str, message: str, letters: str = LETTERS) -> str:
    return translate_message(key, message, False, letters)


def translate_email(key: str, email: str, encrypt: bool = True):
    local, domain_tld = email.split("@")
    domain, tld = domain_tld.split(".")
    return (f"{translate_message(key, local, encrypt, EMAIL_LOCAL_LETTERS)}@"
            f"{translate_message(key, domain, encrypt, DOMAIN_LETTERS)}.{tld}")


def encrypt_email(key: str, email: str):
    return translate_email(key, email, True)


def decrypt_email(key: str, email: str):
    return translate_email(key, email, False)


def numerize_key(key: str) -> int:
    return sum([ord(key[i]) * 12 ** (i + 1) for i in range(len(key))])


def translate_type_match(key: str, message: str, encrypt: bool = True) -> str:
    """Translate numbers to numbers and chars to chars."""
    translated = []

    key_index = 0
    for symbol in message:
        is_symbol_number = symbol in NUMBERS
        letters = NUMBERS if is_symbol_number else LETTERS_UPPER
        actual_key = key if not is_symbol_number else str(ord(key[key_index]))[-1]

        num = letters.find(symbol)
        if num != -1:
            num += (1 if encrypt else -1) * letters.find(actual_key)
            num %= len(letters)

            translated.append(letters[num])

            key_index += 1
            if key_index == len(key):
                key_index = 0
        else:
            translated.append(symbol)

    return "".join(translated)


def translate_IBAN(key: str, IBAN: str, encrypt: bool = True) -> str:
    return IBAN[:4].upper() + translate_type_match(key, IBAN[4:].upper(), encrypt)
