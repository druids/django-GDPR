from typing import Callable

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.test import TestCase

from gdpr.models import AnonymizedData
from germanium.tools import assert_false, assert_true


class NotImplementedMixin(TestCase):
    def assertNotImplemented(self, func: Callable, *args, **kwargs) -> None:
        try:
            func(*args, **kwargs)
        except AssertionError as exc:
            print("NOT IMPLEMENTED:", self.id(), exc)
        else:
            raise AssertionError("Function Implemented successfully!!")

    def assertNotImplementedNotEqual(self, *args, **kwargs):
        self.assertNotImplemented(self.assertNotEqual, *args, **kwargs)


class AnonymizedDataMixin(TestCase):
    def assertAnonymizedDataExists(self, obj: Model, field: str):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        assert_true(
            AnonymizedData.objects.filter(content_type=content_type, object_id=str(obj.pk), field=field).exists())

    def assertAnonymizedDataNotExists(self, obj: Model, field: str):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        assert_false(
            AnonymizedData.objects.filter(content_type=content_type, object_id=str(obj.pk), field=field).exists())
