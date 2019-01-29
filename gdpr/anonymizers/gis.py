import warnings

from gdpr.anonymizers.base import FieldAnonymizer


class GISPointFieldAnonymizer(FieldAnonymizer):
    """
    Anonymizer for PointField from django-gis.

    @TODO: Implement
    """

    def get_anonymized_value(self, value):
        warnings.warn("GISPointFieldAnonymizer is not yet implemented.", UserWarning)
        value.x += 10
        value.y += 10
        return value
