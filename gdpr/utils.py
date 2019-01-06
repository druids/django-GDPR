from typing import Any

from django.core.exceptions import ImproperlyConfigured


def str_to_class(class_string: str) -> Any:
    module_name, class_name = class_string.rsplit('.', 1)
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), [str(class_name)])
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


class AnonymizationModelMixin:
    def anonymize_obj(self):
        from gdpr.loading import register
        if self.__class__ in register:
            register[self.__class__]().anonymize_obj(self)
        else:
            raise ImproperlyConfigured("%s does not have registred anonymizer." % self.__class__)
