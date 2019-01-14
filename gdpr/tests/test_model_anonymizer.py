from unittest.mock import MagicMock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from gdpr.anonymizers import ModelAnonymizer


class TestFieldsParsing(TestCase):
    def setUp(self):
        self.anonymizer = ModelAnonymizer()
        self.field_mock = MagicMock()
        self.anonymizer.fields = self.field_mock

    def test_local_fields_all(self):
        fields = "__ALL__"
        local_fields = self.anonymizer.get_local_fields(fields)

        self.assertEqual(local_fields, self.field_mock.keys())

    def test_local_fields_normal(self):
        fields = ("foo", "bar")
        local_fields = self.anonymizer.get_local_fields(fields)

        self.assertListEqual(local_fields, ["foo", "bar"])

    def test_local_fields_with_related(self):
        fields = ("foo", "bar", ("lorem", "__ALL__"))
        local_fields = self.anonymizer.get_local_fields(fields)

        self.assertListEqual(local_fields, ["foo", "bar"])

    def test_local_fields_empty(self):
        fields = ()
        local_fields = self.anonymizer.get_local_fields(fields)

        self.assertListEqual(local_fields, [])

    def test_local_fields_empty_with_related(self):
        fields = (("lorem", "__ALL__"),)
        local_fields = self.anonymizer.get_local_fields(fields)

        self.assertListEqual(local_fields, [])

    def test_local_fields_malformed(self):
        fields = ("foo", "bar", 1)

        self.assertRaises(ImproperlyConfigured, self.anonymizer.get_local_fields, fields)

    def test_related_fields_all(self):
        fields = (("lorem", "__ALL__"),)
        related_fields = self.anonymizer.get_related_fields(fields)

        self.assertDictEqual(related_fields, {"lorem": "__ALL__"})

    def test_related_fields_normal(self):
        fields = (("lorem", ("ipsum", "dolor")),)
        related_fields = self.anonymizer.get_related_fields(fields)

        self.assertDictEqual(related_fields, {"lorem": ("ipsum", "dolor")})

    def test_related_fields_malformed(self):
        fields = (("lorem", ("ipsum", "dolor"), "foo"),)

        self.assertRaises(ImproperlyConfigured, self.anonymizer.get_related_fields, fields)

    def test_related_fields_with_local(self):
        fields = ("foo", "bar", ("lorem", ("ipsum", "dolor")))
        related_fields = self.anonymizer.get_related_fields(fields)

        self.assertDictEqual(related_fields, {"lorem": ("ipsum", "dolor")})

    def test_related_fields_empty(self):
        fields = ()
        related_fields = self.anonymizer.get_related_fields(fields)

        self.assertDictEqual(related_fields, {})

    def test_related_fields_empty_with_local(self):
        fields = ("foo", "bar")
        related_fields = self.anonymizer.get_related_fields(fields)

        self.assertDictEqual(related_fields, {})
