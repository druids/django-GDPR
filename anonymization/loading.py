import six

from collections import OrderedDict

from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.utils.encoding import force_text

from is_core.utils import str_to_class


class AppAnonymizerLoader:
    """
    Anonymizers loader that interates over all applications and is looks for anonymizers.py file that should contain
    anonymizer classes.
    """

    def import_anonymizers(self):
        for app in apps.get_app_configs():
            try:
                import_module('{}.anonymizers'.format(app.name))
            except ImportError as ex:
                if ((six.PY2 and force_text(ex) != 'No module named anonymizers') or
                        (six.PY3 and force_text(ex) != 'No module named \'{}.anonymizers\''.format(app.name))):
                    raise ex


class AnonymizersRegister:
    """
    Register is storage for found anonymizer classes.
    """

    def __init__(self):
        self.anonymizers = OrderedDict()

    def register_anonymizer(self, model, anonymizer):
        self.anonymizers[model] = anonymizer

    def _init_anonymizers(self):
        for loader_path in settings.ANONYMIZATION_LOADERS:
            if isinstance(loader_path, (list, tuple)):
                for path in loader_path:
                    import_module(path)
            else:
                str_to_class(loader_path)().import_anonymizers()

    def get_anonymizers(self):
        self._init_anonymizers()

        for anonymizer in self.anonymizers.values():
            yield anonymizer


register = AnonymizersRegister()
get_anonymizers = register.get_anonymizers
