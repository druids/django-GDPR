from django.contrib.gis.geos import Point
from django.test import TestCase

from gdpr.anonymizers import GISPointFieldAnonymizer


class TestGISPointFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = GISPointFieldAnonymizer()
        cls.field._encryption_key = 'LoremIpsumDolorSitAmet'

    def test_point_base(self):
        point = Point(1, 1)
        out = self.field.get_encrypted_value(point)

        self.assertNotEqual(point.tuple, out.tuple)

        out_decrypted = self.field.get_decrypted_value(out)

        self.assertTupleEqual(point.tuple, out_decrypted.tuple)
