from decimal import Decimal
from typing import Union

from django.utils.translation import gettext as _

__all__ = ('encrypt_text', 'decrypt_text', 'encrypt_email_address', 'decrypt_email_address', 'numerize_key', 'NUMBERS',
           'LETTERS_UPPER', 'LETTERS_ONLY', 'ALL_CHARS', 'SYMBOLS', 'LETTERS_ALL', 'LETTERS_ALL_WITH_SPACE',
           'NUMBERS_WITHOUT_ZERO', 'JSON_SAFE_CHARS', 'translate_text', 'translate_email_address', 'translate_iban',
           'translate_number')

# Vigenere like Cipher (Polyalphabetic Substitution Cipher)

NUMBERS_WITHOUT_ZERO = '123456789'
NUMBERS = '1234567890'
LETTERS_ONLY = 'abcdefghijklmnopqrstuvwxyz'
LETTERS_UPPER = LETTERS_ONLY.upper()
LETTERS_ALL = LETTERS_ONLY + LETTERS_UPPER
LETTERS_ALL_WITH_SPACE = LETTERS_ALL + ' '
SYMBOLS = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
# Translators: You can add special characters of your language at the end
ALL_CHARS = _(' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
# Translators: You can add special characters of your language at the end
JSON_SAFE_CHARS = _(' !#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~')

# https://en.wikipedia.org/wiki/Email_address#Syntax
RESTRICTED_EMAIL_LOCAL_CHARS = LETTERS_ONLY + NUMBERS + '_-'
EMAIL_LOCAL_CHARS = '!#$%&\'*+-/0123456789=?ABCDEFGHIJKLMNOPQRSTUVWXYZ^_`abcdefghijklmnopqrstuvwxyz{|}~'
DOMAIN_CHARS = LETTERS_ONLY + NUMBERS  # RFC952 + RFC1123


def translate_text(key: str, text: str, encrypt: bool = True, alphabet: str = ALL_CHARS) -> str:
    """
    Translate text based on polyalphabetic substitution cipher based on Vigenere's cipher.

    Notes
        * When the ``translate_text`` encounters a char which is not included in the alphabet the char is skipped and
          left unchanged therefore it is recommended to use on CharFieldAnonymizer the ``transliterate`` option or do
          this yourself on your own anonymizer with method ``unidecode.unidecode``.

    Examples:
        * ``translate_text('LoremIpsum', 'Hello World')`` -> ``'tU_R]IHchZ1'``
        * ``translate_text('LoremIpsum', 'tU_R]IHchZ1', encrypt=False)`` -> ``'Hello World'``
        * ``translate_text('LoremIpsum', 'Hello World', alphabet=LETTERS_ALL)`` -> ``'Hdzcs Waqav'``
        * ``translate_text('LoremIpsum', 'Hdzcs Waqav', encrypt=False, alphabet=LETTERS_ALL)`` -> ``'Hello World'``

    Args:
        key: The encryption key to be used to encrypt or decrypt message
        text: The text to be encrypted or decrypted
        encrypt: If ``True`` the function encrypts the text. If ``False`` the function decrypts the text.
        alphabet: The "alphabet" to be used for encryption thanks to this you can encrypt for example only numbers.

    Returns:
        Encrypted or decrypted text

    """
    translated = []

    key_index = 0
    for char in text:
        num = alphabet.find(char)
        if num != -1:
            num += (1 if encrypt else -1) * alphabet.find(key[key_index])
            num %= len(alphabet)

            translated.append(alphabet[num])

            key_index += 1
            if key_index == len(key):
                key_index = 0
        else:
            translated.append(char)

    return "".join(translated)


def encrypt_text(key: str, text: str, alphabet: str = ALL_CHARS) -> str:
    """
    Encrypts text based on polyalphabetic substitution cipher based on Vigenere's cipher.

    Notes
        * When the ``encrypt_text`` encounters a char which is not included in the alphabet the char is skipped and
          left unchanged therefore it is recommended to use on CharFieldAnonymizer the ``transliterate`` option or
          do this yourself on your own anonymizer with method `unidecode.unidecode`.

    Examples:
        * ``encrypt_text('LoremIpsum', 'Hello World')`` -> ``'tU_R]IHchZ1'``
        * ``encrypt_text('LoremIpsum', 'Hello World', alphabet=LETTERS_ALL)`` -> ``'Hdzcs Waqav'``

    See Also:
        * ``gdpr.encryption.translate_text``
        * ``gdpr.encryption.decrypt_text``

    Args:
        key: The encryption key
        text: The plaintext to be encrypted
        alphabet: The "alphabet" to be used for encryption thanks to this you can encrypt for example only numbers.

    Returns:
        Ciphertext - Encrypted text

    """
    return translate_text(key, text, True, alphabet)


def decrypt_text(key: str, text: str, alphabet: str = ALL_CHARS) -> str:
    """
    Decrypts text based on polyalphabetic substitution cipher based on Vigenere's cipher.

    Notes
        * When the ``decrypt_text`` encounters a char which is not included in the alphabet the char is skipped and
          left unchanged therefore it is recommended to use on CharFieldAnonymizer the ``transliterate`` option or do
          this yourself on your own anonymizer with method `unidecode.unidecode`.

    Examples:
        * ``decrypt_text('LoremIpsum', 'tU_R]IHchZ1')`` -> ``'Hello World'``
        * ``decrypt_text('LoremIpsum', 'Hdzcs Waqav`', alphabet=LETTERS_ALL)` ->``'Hello World'``

    See Also:
            * ``gdpr.encryption.translate_text``
            * ``gdpr.encryption.encrypt_text``

    Args:
        key: The encryption key
        text: The ciphertext to be decrypted
        alphabet: The "alphabet" to be used for encryption thanks to this you can encrypt for example only numbers.

    Returns:
        Plaintext - Decrypted text

    """
    return translate_text(key, text, False, alphabet)


def translate_email_address(key: str, email: str, encrypt: bool = True, restricted_mode: bool = True):
    """
    Translate email address based on polyalphabetic substitution cipher based on Vigenere's cipher.

    Examples:
        * ``translate_email_address('LoremIpsum', 'foo@bar.com')`` -> ``'-_b@ao9.com'``
        * ``translate_email_address('LoremIpsum', '-_b@ao9.com', encrypt=False)`` -> ``'foo@bar.com'``

    Notes:
        * The first part of the email address in non restricted mode is translated based on RFC5322, RFC5321, RFC3696
          and domain name on RFC952 + RFC1123
        * The translations skips dots (``.``) as they cannot be at the begging or end.
        * The TLD (Top level domain) is not translated to serve statistical purposes.

    Warnings:
        * The translation method *does not support* comments or IP address in the domain part of the email e.g.: Formats
          ``jsmith@[192.168.2.1]`` or ``jsmith@[IPv6:2001:db8::1]`` and
          ``john.smith@(comment)example.com`` or ``john.smith@example.com(comment)`` are not supported.
        * The input is not being checked for correct format.

    See Also:
        * ``gdpr.encryption.translate_text``
        * https://en.wikipedia.org/wiki/Email_address#Local-part

    Args:
        key: The encryption key
        email: The email address to be encrypted or decrypted
        encrypt: If ``True`` the function encrypts the email. If ``False`` the function decrypts the email.
        restricted_mode: Some email clients such as Windows Live Hotmail does not permit special characters despite
                         their standardized used. If this option is ``True`` encryption will use only alphanumeric
                         chars, underscore(``_``) and hyphen (``-``).

    Returns:
        Encrypted or decrypted email address

    """
    local, domain_tld = email.split("@")
    domain, tld = domain_tld.rsplit(".", 1)
    if not restricted_mode:
        return (f'{translate_text(key, local, encrypt, EMAIL_LOCAL_CHARS)}@'
                f'{translate_text(key, domain, encrypt, DOMAIN_CHARS)}.{tld}')
    else:
        return (f'{translate_text(key, local, encrypt, RESTRICTED_EMAIL_LOCAL_CHARS)}@'
                f'{translate_text(key, domain, encrypt, DOMAIN_CHARS)}.{tld}')


def encrypt_email_address(key: str, email: str, restricted_mode: bool = True):
    """
    Encrypts email address based on polyalphabetic substitution cipher based on Vigenere's cipher.

    Examples:
        * ``encrypt_email_address('LoremIpsum', 'foo@bar.com')`` -> ``'-_b@ao9.com'``

    Notes:
        * The first part of the email address in non restricted mode is translated based on RFC5322, RFC5321, RFC3696
          and domain name on RFC952 + RFC1123
        * The translations skips dots (``.``) as they cannot be at the begging or end.
        * The TLD (Top level domain) is not translated to serve statistical purposes.

    Warnings:
        * The translation method *does not support* comments or IP address in the domain part of the email e.g.: Formats
          ``jsmith@[192.168.2.1]`` or ``jsmith@[IPv6:2001:db8::1]`` and
          ``john.smith@(comment)example.com`` or ``john.smith@example.com(comment)`` are not supported.
        * The input is not being checked for correct format.

    See Also:
        * ``gdpr.encryption.translate_text``
        * ``gdpr.encryption.translate_email_address``
        * ``gdpr.encryption.decrypt_email_address``
        * https://en.wikipedia.org/wiki/Email_address#Local-part

    Args:
        key: The encryption key
        email: The email address to be encrypted
        restricted_mode: Some email clients such as Windows Live Hotmail does not permit special characters despite
                         their standardized used. If this option is `True` encryption will use only alphanumeric chars,
                         underscore(``_``) and hyphen (``-``).

    Returns:
        Encrypted email address

    """
    return translate_email_address(key, email, True, restricted_mode)


def decrypt_email_address(key: str, email: str, restricted_mode: bool = True):
    """
    Decrypts email address based on polyalphabetic substitution cipher based on Vigenere's cipher.

    Examples:
        * ``decrypt_email_address('LoremIpsum', '-_b@ao9.com')`` -> ``'foo@bar.com'``

    Notes:
        * The first part of the email address in non restricted mode is translated based on RFC5322, RFC5321, RFC3696
          and domain name on RFC952 + RFC1123
        * The translations skips dots (``.``) as they cannot be at the begging or end.
        * The TLD (Top level domain) is not translated to serve statistical purposes.

    Warnings:
        * The translation method *does not support* comments or IP address in the domain part of the email e.g.: Formats
          ``jsmith@[192.168.2.1]`` or ``jsmith@[IPv6:2001:db8::1]`` and
          ``john.smith@(comment)example.com`` or ``john.smith@example.com(comment)`` are not supported.
        * The input is not being checked for correct format.

    See Also:
        * ``gdpr.encryption.translate_text``
        * ``gdpr.encryption.translate_email_address``
        * ``gdpr.encryption.encrypt_email_address``
        * https://en.wikipedia.org/wiki/Email_address#Local-part

    Args:
        key: The encryption key
        email: The email address to be encrypted or decrypted
        encrypt: If ``True`` the function encrypts the email. If ``False`` the function decrypts the email.
        restricted_mode: Some email clients such as Windows Live Hotmail does not permit special characters despite
                         their standardized used. If this option is `True` encryption will use only alphanumeric chars,
                         underscore(``_``) and hyphen (``-``).

    Returns:
        Decrypted email address

    """
    return translate_email_address(key, email, False, restricted_mode)


def numerize_key(key: str) -> int:
    """
    Blackbox function for generating some big number from str.

    Examples:
        * ``numerize_key('LoremIpsum')`` -> ``7406395466880``
        * ``numerize_key('LoremIpsumDolorSitAmet')`` -> ``69127628581563401652806784``

    Notes:
        In case you are really wondering how this function works. The algorithm is following:
        1. Each letter convert to ascii code number
        2. Multiply each number by ``42``
        3. we multiple each number by ten to the power of it's position (first position is 0)
        5. We sum all numbers

    Args:
        key: String encryption key

    Returns:
        Big whole number to be used as encryption key

    """
    return sum([ord(key[i]) * 42 ** (i + 1) for i in range(len(key))])


def translate_type_match(key: str, text: str, encrypt: bool = True, numbers: str = NUMBERS,
                         alphabet: str = LETTERS_ALL) -> str:
    """
    Translate text while retaining type (char, number) based on polyalphabetic substitution cipher.

    Examples:
        * ``translate_type_match('LoremIpusm', 'CZ20180612')`` -> ``'BY50901250'``
        * ``translate_type_match('LoremIpusm', 'BY50901250', encrypt=False)`` -> ``'CZ20180612'``

    See Also:
        * ``gdpr.encryption.translate_text``

    Args:
        key: The encryption key
        text: The text to be encrypted or decrypted
        encrypt: If ``True`` the function encrypts the text. If ``False`` the function decrypts the text.
        numbers: The "alphabet" used to translate numbers.
        alphabet: The "alphabet" used to translate letters.

    Returns:
        Encrypted or decrypted text

    """
    translated = []

    key_index = 0
    for char in text:
        is_symbol_number = char in numbers
        alphabet = numbers if is_symbol_number else alphabet
        actual_key = key if not is_symbol_number else str(ord(key[key_index]))[-1]

        num = alphabet.find(char)
        if num != -1:
            num += (1 if encrypt else -1) * alphabet.find(actual_key)
            num %= len(alphabet)

            translated.append(alphabet[num])

            key_index += 1
            if key_index == len(key):
                key_index = 0
        else:
            translated.append(char)

    return "".join(translated)


def translate_iban(key: str, iban: str, encrypt: bool = True) -> str:
    """
    Translate IBAN using ``translate_type_match`` function.

    Warnings:
        * This method only encrypts the numbers and letters, therefore output of this function will have IBAN format
          but will not pass any additional validations. If you need this used localised smart Anonymizer as
          IBAN validation is country specific.

    See Also:
        * ``gdpr.encryption.translate_text``
        * ``gdpr.encryption.translate_type_match``

    Examples:
        * ``translate_iban('LoremIpsum', 'CZ65 0800 0000 1920 0014 5399')`` - > ``'CZ15 3882 1468 6950 8228 1149'``
        * ``translate_iban('LoremIpsum', 'CZ15 3882 1468 6950 8228 1149', encrypt=False)`` ->
          ``'CZ65 0800 0000 1920 0014 5399'``
        * ``translate_iban('LoremIpsum', 'GB29NWBK60161331926819')`` -> ``'GB79MVAJ74746361747277'``
        * ``translate_iban('LoremIpsum', 'GB79MVAJ74746361747277', encrypt=False)`` -> ``'GB29NWBK60161331926819'``

    Args:
        key: The encryption key
        iban: The IBAN to be encrypted or decrypted
        encrypt: If ``True`` the function encrypts the text. If ``False`` the function decrypts the text.

    Returns:
        Encrypted or decrypted IBAN

    """
    return iban[:2].upper() + translate_type_match(key, iban[2:].upper(), encrypt, alphabet=LETTERS_UPPER)


def translate_number(key: str, number: Union[Decimal, int], encrypt: bool = True):
    """
    Takes number converts it to string and translate it using ``translate_text`` with num alphabet.

    Args:
        key: The encryption key
        number: The number Decimal or int to be translated
        encrypt: If ``True`` the function encrypts the text. If ``False`` the function decrypts the text.

    Returns:
        Encrypted number

    """
    original_type = type(number)
    str_number = str(number)
    if "-" in str_number:
        if "." in str_number:
            return original_type(
                str_number[0] + translate_text(
                    key, str_number[1], encrypt=encrypt, alphabet=NUMBERS_WITHOUT_ZERO
                ) + translate_text(
                    key, str_number[2:-1], encrypt=encrypt, alphabet=NUMBERS
                ) + translate_text(key, str_number[-1], encrypt=encrypt, alphabet=NUMBERS_WITHOUT_ZERO)
            )
        else:
            return original_type(
                str_number[0] + translate_text(
                    key, str_number[1], encrypt=encrypt, alphabet=NUMBERS_WITHOUT_ZERO
                ) + translate_text(key, str_number[2:], encrypt=encrypt, alphabet=NUMBERS)
            )
    else:
        if "." in str_number:
            return original_type(
                translate_text(
                    key, str_number[0], encrypt=encrypt, alphabet=NUMBERS_WITHOUT_ZERO
                ) + translate_text(
                    key, str_number[1:-1], encrypt=encrypt, alphabet=NUMBERS
                ) + translate_text(key, str_number[-1], encrypt=encrypt, alphabet=NUMBERS_WITHOUT_ZERO)
            )
        else:
            return original_type(
                translate_text(
                    key, str_number[0], encrypt=encrypt, alphabet=NUMBERS_WITHOUT_ZERO
                ) + translate_text(key, str_number[1:], encrypt=encrypt, alphabet=NUMBERS)
            )
