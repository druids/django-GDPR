import hashlib
from typing import Any

from gdpr.anonymizers.base import FieldAnonymizer


class BaseHashTextFieldAnonymizer(FieldAnonymizer):
    algorithm: str
    is_reversible = False

    def get_encrypted_value(self, value: Any, encryption_key: str):
        h = hashlib.new(self.algorithm)
        h.update(value.encode('utf-8'))
        return h.hexdigest()[:len(value)] if value else value


class MD5TextFieldAnonymizer(BaseHashTextFieldAnonymizer):
    algorithm = 'md5'


class SHA256TextFieldAnonymizer(BaseHashTextFieldAnonymizer):
    algorithm = 'sha256'


class HashTextFieldAnonymizer(BaseHashTextFieldAnonymizer):

    def __init__(self, algorithm: str, *args, **kwargs):
        if algorithm not in hashlib.algorithms_guaranteed:
            raise RuntimeError(f'Hash algorithm {algorithm} is not supported by python hashlib.')
        self.algorithm = algorithm

        super().__init__(*args, **kwargs)
