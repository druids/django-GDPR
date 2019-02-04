import warnings

from django.contrib.gis.geos import Point

from gdpr.anonymizers.base import FieldAnonymizer, NumericFieldAnonymizer


class GISPointFieldAnonymizer(NumericFieldAnonymizer):
    """
    Anonymizer for PointField from django-gis.
    """

    def get_encrypted_value(self, value: Point) -> Point:
        new_value: Point = Point(value.tuple)
        new_value.x += self.get_numeric_encryption_key(int(new_value.x))
        new_value.y += self.get_numeric_encryption_key(int(new_value.y))

        return new_value

    def get_decrypted_value(self, value: Point) -> Point:
        new_value: Point = Point(value.tuple)
        new_value.x -= self.get_numeric_encryption_key(int(new_value.x))
        new_value.y -= self.get_numeric_encryption_key(int(new_value.y))

        return new_value
