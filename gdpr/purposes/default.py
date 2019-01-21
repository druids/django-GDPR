from typing import Any, Optional, TYPE_CHECKING, Tuple, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from gdpr.loading import anonymizer_register

if TYPE_CHECKING:
    from gdpr.models import LegalReason


class PurposeMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        from gdpr.loading import purpose_register

        new_class = super(PurposeMetaclass, mcs).__new__(mcs, name, bases, attrs)
        if hasattr(new_class, 'slug') and new_class.slug:
            if new_class.slug in purpose_register:
                raise ImproperlyConfigured('More anonymization purposes with slug {}'.format(new_class.slug))

            purpose_register.register_purpose(new_class.slug, new_class, new_class.source_model)
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
    anonymize_legal_reason_related_objects_only: bool = False  # @TODO: Add support

    def anonymize_obj(self, obj: Model, legal_reason: Optional["LegalReason"] = None,
                      fields: Optional[Union[str, Tuple[Any, ...]]] = None):
        anonymizer_register[self.source_model]().anonymize_obj(obj, legal_reason, self, fields or self.fields)
