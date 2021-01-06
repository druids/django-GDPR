from typing import Any, Type

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model, QuerySet


def str_to_class(class_string: str) -> Any:
    module_name, class_name = class_string.rsplit('.', 1)
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), [str(class_name)])
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def get_number_guess_len(value):
    """
    Safety measure against key getting one bigger (overflow) on decrypt e.g. (5)=1 -> 5 + 8 = 13 -> (13)=2
    Args:
        value: Number convertible to int to get it's length

    Returns:
        The even length of the whole part of the number
    """
    guess_len = len(str(int(value)))
    return guess_len if guess_len % 2 != 0 else (guess_len - 1)


def get_field_or_none(model: Type[Model], field_name: str):
    """
    Use django's _meta field api to get field or return None.

    Args:
        model: The model to get the field on
        field_name: The name of the field

    Returns:
        The field or None

    """
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


"""
Enable support for druids reversion fork
"""


def get_reversion_versions(obj: Any) -> QuerySet:
    from reversion.models import Version
    from django.contrib.contenttypes.models import ContentType

    return Version.objects.get_for_object(obj)


def get_reversion_version_model(version) -> Type[Model]:
    """Get object model of the version."""
    if hasattr(version, '_model'):
        return version._model
    return version.content_type.model_class()


def get_reversion_local_field_dict(obj):
    if hasattr(obj, '_local_field_dict'):
        return obj._local_field_dict
    return obj.flat_field_dict


def is_reversion_installed():
    try:
        import reversion
        return True
    except ImportError:
        return False
