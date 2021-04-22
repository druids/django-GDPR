from typing import Optional

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from .base import RelationAnonymizer


class ReverseGenericRelationAnonymizer(RelationAnonymizer):
    """Defines relation for anonymizer to cope with GenericForeignKey."""

    app_name: str
    model_name: str
    content_type_field: str
    id_field: str

    def __init__(self, app_name: str, model_name: Optional[str] = None, content_type_field: str = 'content_type',
                 id_field: str = 'object_id'):
        """

        :param app_name: The name of the app or `<app_name>.<model_name>`
        :param model_name: The name of the model with GenericRelation
        :param content_type_field: The name of the FK to ContentType Model
        :param id_field: The id of the related model
        """
        if model_name is None:
            self.app_name, self.model_name = app_name.split('.')
        else:
            self.app_name = app_name
            self.model_name = model_name
        self.content_type_field = content_type_field
        self.id_field = id_field

        super().__init__()

    def get_related_objects(self, obj):
        return self.get_related_model().objects.filter(
            **{self.content_type_field: ContentType.objects.get_for_model(obj), self.id_field: obj.pk}
        )

    def get_related_model(self):
        return apps.get_model(self.app_name, self.model_name)


class GenericRelationAnonymizer(RelationAnonymizer):
    """Defines relation for anonymizer to cope with GenericForeignKey."""

    app_name: str
    model_name: str
    content_object_field: str

    def __init__(self, app_name: str, model_name: Optional[str] = None, content_object_field: str = 'content_object'):
        """

        :param app_name: The name of the app or `<app_name>.<model_name>`
        :param model_name: The name of the model with GenericRelation
        :param content_type_field: The name of the FK to ContentType Model
        :param id_field: The id of the related model
        """
        if model_name is None:
            self.app_name, self.model_name = app_name.split('.')
        else:
            self.app_name = app_name
            self.model_name = model_name
        self.content_object_field = content_object_field

        super().__init__()

    def get_related_objects(self, obj):
        model: Model = self.get_related_model()
        content_obj = getattr(obj, self.content_object_field, None)
        if content_obj is None:
            return model.objects.none()
        if isinstance(content_obj, model):
            return [content_obj]
        return model.objects.none()

    def get_related_model(self):
        return apps.get_model(self.app_name, self.model_name)
