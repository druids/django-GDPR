import os

from os.path import basename

import re

import hashlib

from django.conf import settings
from django.core.files.base import ContentFile

from chamber.utils import remove_accent


class FieldAnonymizer:
    """
    Field anonymizer's purpose is to anonymize model field accoding to defined rule.
    """

    ignore_empty_values = True
    empty_values = [None]

    def __init__(self, ignore_empty_values=None, empty_values=None):
        """
        @param ignore_empty_values: defines if empty value of a model will be ignored or should be anonymized too
        @param empty_values: define list of values which are considered as empty
        """
        self._ignore_empty_values = ignore_empty_values if ignore_empty_values is not None else self.ignore_empty_values
        self._empty_values = empty_values if empty_values is not None else self.empty_values

    def get_anonymized_value_from_obj(self, obj, name):
        value = getattr(obj, name)
        if self._ignore_empty_values and value in self._empty_values:
            return value
        else:
            return self.get_anonymized_value(value)

    def get_anonymized_value(self, value):
        """
        There must be defined implementation of rule for anonymization
        @param value: value that is anonymized
        @return: anonymized value
        """
        raise NotImplementedError


class MD5TextFieldAnonymizer(FieldAnonymizer):
    """
    Simple anonymizer that converts input string value to the MD5 hash.
    Final anonymized value maximal length will be 32 but if input value length is lower
    the anonymized string length is the same as input value.
    """

    empty_values = [None, '']

    def get_anonymized_value(self, value):
        return hashlib.md5(value.encode('utf-8')).hexdigest()[:len(value)] if value else value


class EmailFieldAnonymizer(FieldAnonymizer):
    """
    E-mail anonymizer that anonymizes address according to HC method.
    It uses MD5 hash of whole e-mail joined with non existent domain "devnull.homecredit.net".
    """

    empty_values = [None, '']

    def get_anonymized_value(self, value):
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

    def get_anonymized_value(self, value):
        site_id, email = value.split(':', 1)
        return '{}:{}'.format(site_id, super().get_anonymized_value(email))


class NameFieldAnonymizer(FieldAnonymizer):
    """
    Anonymization of first name and last name of the customer with HC method. There is used Ceasar cipher.
    There is used only 26 characters [A-Z] and space. Chars that are not space or cannot be converted from UTF-8 to
    the [A-Z] are replaced with char "Q".
    """

    empty_values = [None, '']

    def _char_to_number(char_value):
        return ord(char_value) - 64

    def _number_to_char(int_value):
        return chr((int_value % 27) + 64)

    def get_anonymized_value(self, value):
        normalized_value = re.sub(r'[^A-Z ]', 'Q', remove_accent(value.strip()).upper())
        normalized_key = (
            settings.ANONYMIZATION_NAME_KEY[i % len(settings.ANONYMIZATION_NAME_KEY)]
            for i in range(len(normalized_value))
        )

        return ''.join([
            v if v == ' ' else self._number_to_char(self._char_to_number(v) + int(k))
            for k, v in zip(normalized_key, normalized_value)
        ])


class PhoneFieldAnonymizer(FieldAnonymizer):
    """
    Phone number which is anonymized with HC method. To the phone number without calling code, numeric key is added.
    """

    ignore_empty_values = False

    def get_anonymized_value(self, value):
        return value[0:4] + '{0:09}'.format((int(value[4:]) + settings.ANONYMIZATION_PHONE_KEY) % 1000000000)


class PersonalIIDFieldAnonymizer(FieldAnonymizer):
    """
    Personal ID anonymizer uses similar method like phone. To the personal ID control number is added numeric key.
    """

    empty_values = [None, '']

    def get_anonymized_value(self, value):
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

    def get_anonymized_value(self, value):
        return str(int(hashlib.md5(value.encode('utf-8')).hexdigest(), 16))[:9]


class DummyFileAnonymizer(FieldAnonymizer):
    """
    File anonymizer that replaces file with a anonymized variant.
    """

    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path

    def get_anonymized_value(self, value):
        with open(os.path.join(settings.ANONYMIZATION_PATH, self.file_path), mode='rb') as f:
            content = f.read()
        value.save(basename(self.file_path), ContentFile(content), save=False)
        return value


class StaticValueAnonymizer(FieldAnonymizer):
    """
    Static value anonymizer replaces value with defined static value.
    """

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    def get_anonymized_value(self, value):
        return self.value


class ModelAnonymizerBase(type):
    """
    Metaclass for anonymizers. The main purpose of the metaclass is to register anonymizers and find field anonymizers
    defined in the class as attributes and store it to the fields property.
    """
    def __new__(cls, name, bases, attrs):
        from anonymization.loading import register

        new_obj = super(ModelAnonymizerBase, cls).__new__(cls, name, bases, attrs)

        # Also ensure initialization is only performed for subclasses of ModelAnonymizer
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelAnonymizerBase)]
        if not parents or not hasattr(new_obj, 'Meta') or getattr(new_obj.Meta, 'abstract', False):
            return new_obj

        fields = {}
        for name, obj in attrs.items():
            if isinstance(obj, FieldAnonymizer):
                fields[name] = obj
        new_obj.fields = fields
        register.register_anonymizer(new_obj.Meta.model, new_obj)
        return new_obj


class ModelAnonymizer(metaclass=ModelAnonymizerBase):
    """
    Default model anonymizer that supports anonymization per object.
    Child must define Meta class with model (like factoryboy)
    """

    can_anonymize_qs = False
    chunk_size = 10000

    def anonymize_obj(self, obj):
        updated_data = {name: field.get_anonymized_value_from_obj(obj, name) for name, field in self.fields.items()}
        obj.__class__.objects.filter(pk=obj.pk).update(**updated_data)


class DeleteModelAnonymizer(ModelAnonymizer):
    """
    The simpliest anonymization class that is used for removing whole input queryset.
    """

    can_anonymize_qs = True

    def anonymize_obj(self, obj):
        obj.__class__.objects.filter(pk=obj.pk).delete()

    def anonymize_qs(self, qs):
        qs.delete()
