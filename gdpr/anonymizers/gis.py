"""Since django 1.11 djnago-GIS requires GDAL."""
import logging

from django.core.exceptions import ImproperlyConfigured
from gdpr.anonymizers.base import NumericFieldAnonymizer

logger = logging.getLogger(__name__)


def is_gis_installed():
    try:
        from django.contrib.gis.geos import Point
    except ImproperlyConfigured:
        return False
    else:
        return True


if not is_gis_installed():
    logger.warning("Unable to load django GIS. GIS anonymization disabled.")


class GISPointFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymizer for PointField from django-gis.
    """

    def get_encrypted_value(self, value):
        if not is_gis_installed():
            raise ImproperlyConfigured('Unable to load django GIS.')
        from django.contrib.gis.geos import Point

        new_value: Point = Point(value.tuple)
        new_value.x += self.get_numeric_encryption_key(int(new_value.x))
        new_value.y += self.get_numeric_encryption_key(int(new_value.y))

        return new_value

    def get_decrypted_value(self, value):
        if not is_gis_installed():
            raise ImproperlyConfigured('Unable to load django GIS.')
        from django.contrib.gis.geos import Point

        new_value: Point = Point(value.tuple)
        new_value.x -= self.get_numeric_encryption_key(int(new_value.x))
        new_value.y -= self.get_numeric_encryption_key(int(new_value.y))

        return new_value
