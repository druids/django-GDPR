from collections import OrderedDict
from importlib import import_module
from typing import Iterator

from django.apps import apps
from django.conf import settings
from django.db.models import Model
from django.utils.encoding import force_text

from gdpr.anonymizers import ModelAnonymizer
from .utils import str_to_class


class AppAnonymizerLoader:
    """
    Anonymizers loader that interates over all applications and is looks for anonymizers.py file that should contain
    anonymizer classes.
    """

    def import_anonymizers(self) -> None:
        for app in apps.get_app_configs():
            try:
                import_module('{}.anonymizers'.format(app.name))
            except ImportError as ex:
                if force_text(ex) != 'No module named \'{}.anonymizers\''.format(app.name):
                    raise ex


class AnonymizersRegister:
    """
    Register is storage for found anonymizer classes.
    """

    def __init__(self):
        self.anonymizers: "OrderedDict[Model, ModelAnonymizer]" = OrderedDict()

    def register_anonymizer(self, model: Model, anonymizer: ModelAnonymizer) -> None:
        self.anonymizers[model] = anonymizer

    def _init_anonymizers(self) -> None:
        for loader_path in getattr(settings, "ANONYMIZATION_LOADERS", ["gdpr.loading.AppAnonymizerLoader"]):
            if isinstance(loader_path, (list, tuple)):
                for path in loader_path:
                    import_module(path)
            else:
                str_to_class(loader_path)().import_anonymizers()

    def get_anonymizers(self) -> Iterator[ModelAnonymizer]:
        self._init_anonymizers()

        for anonymizer in self.anonymizers.values():
            yield anonymizer


register = AnonymizersRegister()
get_anonymizers = register.get_anonymizers
