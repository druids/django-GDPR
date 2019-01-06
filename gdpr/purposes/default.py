from collections import OrderedDict
from typing import Any, Tuple, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

purposes_map: "OrderedDict[str, AbstractPurpose]" = OrderedDict()


class PurposeMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        new_class = super(PurposeMetaclass, mcs).__new__(mcs, name, bases, attrs)
        if hasattr(new_class, 'slug') and new_class.slug:
            if new_class.slug in purposes_map:
                raise ImproperlyConfigured('More anonymization purposes with slug {}'.format(new_class.slug))

            purposes_map[new_class.slug] = new_class
        return new_class

    def __str__(self):
        return str(self.name)


class AbstractPurpose(metaclass=PurposeMetaclass):
    """

    :param anonymize_legal_reason_related_object_only: If True anonymize only related objects which have links which
    have LegalReasonRelatedObject records.
    """

    name: str
    slug: str
    source_model: Model
    fields: Union[str, Tuple[Any, ...]]
    expiration_timedelta: Any
    anonymize_legal_reason_related_objects_only: bool = False
