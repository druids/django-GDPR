from typing import Optional

from .base import RelationAnonymizer


class ReverseGenericRelationAnonymizer(RelationAnonymizer):
    """Defines relation for anonymizer to cope with GenericForeignKey.

    @TODO: Implement!
    """

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
