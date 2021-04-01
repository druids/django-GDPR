from django.test import TestCase

from gdpr.fields import Fields
from germanium.tools import assert_list_equal, assert_true
from tests.anonymizers import CustomerAnonymizer
from tests.models import Customer


LOCAL_FIELDS = ("first_name", "last_name")

BASIC_FIELDS = (
    "primary_email_address",
    ("emails", (
        "email",
    )),
)

MULTILEVEL_FIELDS = (
    ("accounts", (
        "number",
        "owner",
        ("payments", (
            "value",
            "date"
        ))
    )),
)


class TestFields(TestCase):
    def test_local_all(self):
        fields = Fields('__ALL__', Customer)
        assert_list_equal(fields.local_fields, list(CustomerAnonymizer().fields.keys()))

    def test_local(self):
        fields = Fields(LOCAL_FIELDS, Customer)
        assert_list_equal(fields.local_fields, list(LOCAL_FIELDS))

    def test_local_and_related(self):
        fields = Fields(BASIC_FIELDS, Customer)

        assert_list_equal(fields.local_fields, ['primary_email_address'])
        assert_true('emails' in fields.related_fields)
        assert_list_equal(fields.related_fields['emails'].local_fields, ['email'])

    def test_multilevel_related(self):
        fields = Fields(MULTILEVEL_FIELDS, Customer)

        assert_list_equal(fields.local_fields, [])
        assert_true('accounts' in fields.related_fields)
        assert_list_equal(fields.related_fields['accounts'].local_fields, ['number', 'owner'])
        assert_true('payments' in fields.related_fields['accounts'].related_fields)
        assert_list_equal(fields.related_fields['accounts'].related_fields['payments'].local_fields, ['value', 'date'])
