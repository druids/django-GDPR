from typing import Any


def str_to_class(class_string: str) -> Any:
    module_name, class_name = class_string.rsplit('.', 1)
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), [str(class_name)])
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


"""
Enable support for druids reversion fork
"""


def get_reversion_versions(obj):
    from reversion.models import Version
    from django.contrib.contenttypes.models import ContentType

    if hasattr(Version.objects, "get_for_object"):
        return Version.objects.get_for_object(obj).order_by("id")
    content_type = ContentType.objects.get_for_model(obj.__class__)
    return Version.objects.filter(content_type=content_type, object_id=obj.pk).order_by("id")


def get_reversion_local_field_dict(obj):
    if hasattr(obj, "_local_field_dict"):
        return obj._local_field_dict
    return obj.flat_field_dict


def is_reversion_installed():
    try:
        import reversion
        return True
    except ImportError:
        return False
