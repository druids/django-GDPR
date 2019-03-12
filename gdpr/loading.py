from collections import OrderedDict, _OrderedDictItemsView, _OrderedDictKeysView, _OrderedDictValuesView
from importlib import import_module
from typing import TYPE_CHECKING, Any, Generic, Iterator, Optional, Type, TypeVar, Union

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.utils.encoding import force_text

from .utils import str_to_class

if TYPE_CHECKING:
    from gdpr.anonymizers import ModelAnonymizer
    from gdpr.purposes import AbstractPurpose


class BaseLoader:
    """Base class for all loaders."""

    def import_modules(self) -> None:
        raise NotImplementedError


class AppLoader(BaseLoader):
    """Scan all installed apps for `module_name` module."""

    module_name: str

    def import_modules(self) -> None:
        for app in apps.get_app_configs():
            if app.name == 'gdpr':
                continue
            try:
                import_module(f'{app.name}.{self.module_name}')
            except ImportError as ex:
                if force_text(ex) != f'No module named \'{app.name}.{self.module_name}\'':
                    raise ex


class SettingsListLoader(BaseLoader):
    """Import all modules from list `list_name` in settings."""

    list_name: str

    def import_modules(self):
        if not hasattr(settings, self.list_name):
            raise ImproperlyConfigured(f'settings.{self.list_name} not found.')
        modules_list = getattr(settings, self.list_name)
        if type(modules_list) in [list, tuple]:
            for i in modules_list:
                import_module(i)
        else:
            raise ImproperlyConfigured(f'settings.{self.list_name} have incorrect type {str(type(modules_list))}.')


class SettingsListAnonymizerLoader(SettingsListLoader):
    """Load all anonymizers from settings.GDPR_ANONYMIZERS_LIST list."""

    list_name = 'GDPR_ANONYMIZERS_LIST'


class SettingsListPurposesLoader(SettingsListLoader):
    """Load all purposes from settings.GDPR_PURPOSES_LIST list."""

    list_name = 'GDPR_PURPOSES_LIST'


class AppAnonymizerLoader(AppLoader):
    """Scan all installed apps for anonymizers module which should contain anonymizers."""

    module_name = 'anonymizers'


class AppPurposesLoader(AppLoader):
    """Scan all installed apps for purposes module which should contain purposes."""

    module_name = 'purposes'


K = TypeVar('K')
V = TypeVar('V')


class BaseRegister(Generic[K, V]):
    """Base class for all registers."""

    _is_import_done = False
    register_dict: "OrderedDict[K, V]"
    loaders_settings: str
    default_loader: Optional[str]

    def __init__(self):
        self.register_dict = OrderedDict()

    def register(self, key: K, object_class: V) -> None:
        self.register_dict[key] = object_class

    def _import_objects(self) -> None:
        default_loader = [self.default_loader] if self.default_loader else []
        for loader_path in getattr(settings, self.loaders_settings, default_loader):
            if isinstance(loader_path, (list, tuple)):
                for path in loader_path:
                    import_module(path)
            else:
                str_to_class(loader_path)().import_modules()

    def _import_objects_once(self) -> None:
        if self._is_import_done:
            return
        self._is_import_done = True
        self._import_objects()

    def __iter__(self) -> Iterator[V]:
        self._import_objects_once()

        for o in self.register_dict.values():
            yield o

    def __contains__(self, key: K) -> bool:
        self._import_objects_once()

        return key in self.register_dict.keys()

    def __getitem__(self, key: K) -> V:
        self._import_objects_once()

        return self.register_dict[key]

    def keys(self) -> "_OrderedDictKeysView[K]":
        self._import_objects_once()

        return self.register_dict.keys()

    def items(self) -> "_OrderedDictItemsView[K, V]":
        self._import_objects_once()

        return self.register_dict.items()

    def values(self) -> "_OrderedDictValuesView[V]":
        self._import_objects_once()

        return self.register_dict.values()

    def get(self, *args, **kwargs) -> Union[V, Any]:
        self._import_objects_once()

        return self.register_dict.get(*args, **kwargs)


class AnonymizersRegister(BaseRegister[Model, Type["ModelAnonymizer"]]):
    """
    AnonymizersRegister is storage for found anonymizer classes.
    """

    default_loader = 'gdpr.loading.AppAnonymizerLoader'
    loaders_settings = 'ANONYMIZATION_LOADERS'


class PurposesRegister(BaseRegister[str, Type["AbstractPurpose"]]):
    """
    PurposesRegister is storage for found purpose classes.
    """

    default_loader = 'gdpr.loading.AppPurposesLoader'
    loaders_settings = 'PURPOSE_LOADERS'


anonymizer_register = AnonymizersRegister()
purpose_register = PurposesRegister()
