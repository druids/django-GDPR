import hashlib
import os
from os.path import basename

from django.conf import settings
from django.core.files.base import ContentFile

from gdpr.anonymizers.base import FieldAnonymizer


class MD5TextFieldAnonymizer(FieldAnonymizer):
    """
    Simple anonymizer that converts input string value to the MD5 hash.
    Final anonymized value maximal length will be 32 but if input value length is lower
    the anonymized string length is the same as input value.
    """

    empty_values = [None, '']
    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        return hashlib.md5(value.encode('utf-8')).hexdigest()[:len(value)] if value else value


class EmailFieldAnonymizer(FieldAnonymizer):
    """
    E-mail anonymizer that anonymizes address according to HC method.
    It uses MD5 hash of whole e-mail joined with non existent domain "devnull.homecredit.net".
    """

    empty_values = [None, '']
    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        return '{}@{}'.format(
            hashlib.md5(value.lower().encode('utf-8')).hexdigest()[:8],
            'devnull.homecredit.net'
        )


class UsernameFieldAnonymizer(EmailFieldAnonymizer):
    """
    Username must be anonymized with same method as e-mail, but site number, which is first part of username,
    must be preserved.
    """

    ignore_empty_values = False
    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        site_id, email = value.split(':', 1)
        return '{}:{}'.format(site_id, super().get_anonymized_value(email))


class PersonalIIDFieldAnonymizer(FieldAnonymizer):
    """
    Personal ID anonymizer uses similar method like phone. To the personal ID control number is added numeric key.
    """

    empty_values = [None, '']
    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        max_control_number_digits = 4 if len(value) == 10 else 3
        control_number_subtraction = 9999 if len(value) == 10 else 990
        updated_control_number = int(value[6:]) + settings.ANONYMIZATION_PERSONAL_ID_KEY

        return value[:6] + '{{0:0{}}}'.format(max_control_number_digits).format(
            updated_control_number if updated_control_number < 10 ** max_control_number_digits
            else updated_control_number - control_number_subtraction
        )


class IDCardDataFieldAnonymizer(FieldAnonymizer):
    """
    For ID card anonymization, MD5 hash hex digest converted to decadic number is used.
    """

    empty_values = [None, '']
    is_reversible = False

    def get_encrypted_value(self, value, encryption_key):
        return str(int(hashlib.md5(value.encode('utf-8')).hexdigest(), 16))[:9]


class DummyFileAnonymizer(FieldAnonymizer):
    """
    File anonymizer that replaces file with a anonymized variant.
    """

    is_reversible = False

    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path

    def get_encrypted_value(self, value, encryption_key):
        with open(os.path.join(settings.ANONYMIZATION_PATH, self.file_path), mode='rb') as f:
            content = f.read()
        value.save(basename(self.file_path), ContentFile(content), save=False)
        return value
