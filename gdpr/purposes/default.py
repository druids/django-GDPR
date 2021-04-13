from typing import TYPE_CHECKING, Any, Dict, KeysView, List, Optional, Tuple, Type, Union

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, Q
from django.apps import apps
from django.db.models.utils import make_model_tuple

from gdpr.enums import LegalReasonState
from gdpr.fields import Fields
from gdpr.loading import anonymizer_register, purpose_register

if TYPE_CHECKING:
    from gdpr.models import LegalReason
    from gdpr.anonymizers import ModelAnonymizer

FieldList = Union[List[str], Tuple, KeysView[str]]  # List, tuple or return of dict keys() method.
FieldMatrix = Union[str, Tuple[Any, ...]]
RelatedMatrix = Dict[str, FieldMatrix]


class PurposeMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        from gdpr.loading import purpose_register

        new_class = super().__new__(mcs, name, bases, attrs)
        if hasattr(new_class, 'slug') and new_class.slug:
            if new_class.slug in purpose_register:
                raise ImproperlyConfigured('More anonymization purposes with slug {}'.format(new_class.slug))

            purpose_register.register(new_class.slug, new_class)

        def set_source_model_class(model):
            new_class.source_model_class = model

        if isinstance(new_class.source_model_class, str):
            apps.lazy_model_operation(set_source_model_class, make_model_tuple(new_class.source_model_class))

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
    fields: Union[str, Tuple[Any, ...], None] = None
    expiration_timedelta: Any
    anonymize_legal_reason_related_objects_only: bool = False  # @TODO: Add support
    source_model_class: Optional[Union[str, Type[Model]]] = None

    def can_anonymize_obj(self, obj: Model, fields: FieldMatrix):
        return len(fields) != 0

    def get_parsed_fields(self, model: Type[Model]) -> Fields:
        return Fields(self.fields or (), model)

    def deanonymize_obj(self, obj: Model, fields: Optional[FieldMatrix] = None):
        fields = fields or self.fields or ()
        if len(fields) == 0:
            # If there are no fields to deanonymize do nothing.
            return
        obj_model = obj.__class__
        anonymizer: "ModelAnonymizer" = anonymizer_register[obj_model]()
        anonymizer.deanonymize_obj(obj, fields)

    def anonymize_obj(self, obj: Model, legal_reason: Optional["LegalReason"] = None,
                      fields: Optional[FieldMatrix] = None):
        fields = fields or self.fields or ()
        if not self.can_anonymize_obj(obj, fields):
            # If there are no fields to anonymize do nothing.
            return
        from gdpr.models import LegalReason  # noqa

        obj_model = obj.__class__
        anonymizer: "ModelAnonymizer" = anonymizer_register[obj_model]()

        # MultiLegalReason
        other_legal_reasons = LegalReason.objects.filter_source_instance(obj).filter(state=LegalReasonState.ACTIVE)
        if legal_reason:
            other_legal_reasons = other_legal_reasons.filter(~Q(pk=legal_reason.pk))
        if other_legal_reasons.count() == 0:
            anonymizer.anonymize_obj(obj, legal_reason, self, fields)
            return

        from gdpr.loading import purpose_register

        parsed_fields = self.get_parsed_fields(obj_model)

        # Transform legal_reasons to fields
        for allowed_fields in [purpose_register[slug]().get_parsed_fields(obj_model) for slug in
                               set([i.purpose_slug for i in other_legal_reasons])]:
            parsed_fields -= allowed_fields
            if len(parsed_fields) == 0:
                # If there are no fields to anonymize do nothing.
                return

        anonymizer.anonymize_obj(obj, legal_reason, self, parsed_fields)


purposes_map = purpose_register  # Backwards compatibility
