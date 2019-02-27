import os
from os.path import basename

from django.conf import settings
from django.core.files.base import ContentFile

from gdpr.anonymizers.base import FieldAnonymizer


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
