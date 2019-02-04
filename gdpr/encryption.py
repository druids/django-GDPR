from django.utils.translation import gettext as _

__all__ = ["encrypt_message", "decrypt_message", "encrypt_email", "decrypt_email", "numerize_key"]

# Vigenere like Cipher (Polyalphabetic Substitution Cipher)

# Translators: Add special characters of your language at the end
LETTERS = _(" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
# https://en.wikipedia.org/wiki/Email_address#Local-part
EMAIL_LOCAL_LETTERS = "!#$%&'*+-/0123456789=?ABCDEFGHIJKLMNOPQRSTUVWXYZ^_`abcdefghijklmnopqrstuvwxyz{|}~"
DOMAIN_LETTERS = "abcdefghijklmnopqrstuvwxyz0123456789"  # RFC952 + RFC1123

NUMBERS = "1234567890"


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
