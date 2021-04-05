from unittest import skipIf

from django.test import TestCase

from gdpr.anonymizers.gis import ExperimentalGISPointFieldAnonymizer, is_gis_installed
from germanium.tools import assert_not_equal, assert_tuple_equal


class TestGISPointFieldAnonymizer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.field = ExperimentalGISPointFieldAnonymizer(max_x_range=100, max_y_range=100)
        cls.encryption_key = 'LoremIpsumDolorSitAmet'

    @skipIf(not is_gis_installed(), 'Django GIS not available.')
    def test_point_base(self):
        from django.contrib.gis.geos import Point

        point = Point(1, 1)
        out = self.field.get_encrypted_value(point, self.encryption_key)

        assert_not_equal(point.tuple, out.tuple)

        out_decrypted = self.field.get_decrypted_value(out, self.encryption_key)

        assert_tuple_equal(point.tuple, out_decrypted.tuple)
