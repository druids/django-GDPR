"""Since django 1.11 djnago-GIS requires GDAL."""
import logging
from typing import Optional

from django.core.exceptions import ImproperlyConfigured

from gdpr.anonymizers.base import NumericFieldAnonymizer

logger = logging.getLogger(__name__)


def is_gis_installed():
    try:
        from django.contrib.gis.geos import Point
        return True
    except ImproperlyConfigured:
        return False


if not is_gis_installed():
    logger.warning('Unable to load django GIS. GIS anonymization disabled.')


class ExperimentalGISPointFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymizer for PointField from django-gis.

    Warnings:
        May not fully work. Currently works only on positive coordinates.
        With ``max_x_range`` and ``max_y_range`` specified. Also anonymization occurs only on the whole part.
    """

    max_x_range: int
    max_y_range: int

    def __init__(self, max_x_range: Optional[int] = None, max_y_range: Optional[int] = None, *args, **kwargs):
        if max_x_range is not None:
            self.max_x_range = max_x_range
        elif self.max_x_range is None:
            raise ImproperlyConfigured(f'{self.__class__} does not have `max_x_range`.')
        if max_y_range is not None:
            self.max_y_range = max_y_range
        elif self.max_y_range is None:
            raise ImproperlyConfigured(f'{self.__class__} does not have `max_y_range`.')
        super().__init__(*args, **kwargs)

    def get_encrypted_value(self, value, encryption_key: str):
        if not is_gis_installed():
            raise ImproperlyConfigured('Unable to load django GIS.')
        from django.contrib.gis.geos import Point

        new_val: Point = Point(value.tuple)
        new_val.x = (new_val.x + self.get_numeric_encryption_key(encryption_key, int(new_val.x))) % self.max_x_range
        new_val.y = (new_val.y + self.get_numeric_encryption_key(encryption_key, int(new_val.y))) % self.max_y_range

        return new_val

    def get_decrypted_value(self, value, encryption_key: str):
        if not is_gis_installed():
            raise ImproperlyConfigured('Unable to load django GIS.')
        from django.contrib.gis.geos import Point

        new_val: Point = Point(value.tuple)
        new_val.x = (new_val.x - self.get_numeric_encryption_key(encryption_key, int(new_val.x))) % self.max_x_range
        new_val.y = (new_val.y - self.get_numeric_encryption_key(encryption_key, int(new_val.y))) % self.max_y_range

        return new_val
