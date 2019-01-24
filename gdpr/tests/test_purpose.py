from unittest import mock

from django.test import TestCase

from gdpr.purposes.default import AbstractPurpose, PurposeSplitFields
from tests.models import Customer, Email

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

ALL_FIELDS = (
    "__ALL__",
    ("addresses", "__ALL__"),
    ("accounts", (
        "__ALL__",
        ("payments", (
            "__ALL__",
        ))
    )),
    ("emails", (
        "__ALL__",
    )),
)


class TestPurposeFieldDetermination(TestCase):
    def setUp(self):
        self.purpose = AbstractPurpose()
        self.purpose.source_model = Customer

    def test_purpose_split_fields_to_tuple_only_local(self):
        self.assertTupleEqual(PurposeSplitFields(("a",)).get_tuple(), ("a",))

    def test_purpose_split_fields_to_tuple_only_related(self):
        self.assertTupleEqual(PurposeSplitFields(related={"a": ("b",)}).get_tuple(), (("a", ("b",)),))

    def test_purpose_split_fields_to_tuple_both(self):
        self.assertTupleEqual(PurposeSplitFields(("a",), {"b": ("c",)}).get_tuple(), ("a", ("b", ("c",)),))

    def test_purpose_split_fields_to_tuple_all(self):
        self.assertTupleEqual(PurposeSplitFields("__ALL__").get_tuple(), ("__ALL__",))

    def test_purpose_split_fields_to_tuple_all_n_related(self):
        self.assertTupleEqual(PurposeSplitFields("__ALL__", {"b": ("c",)}).get_tuple(), ("__ALL__", ("b", ("c",))))

    def test_split_fields_basic_fields(self):
        fields = self.purpose.split_fields(BASIC_FIELDS)

        self.assertListEqual(fields.local, ["primary_email_address"])
        self.assertDictEqual(fields.related, {"emails": ("email",)})

    def test_split_fields_multilevel_fields(self):
        local, related = self.purpose.split_fields(MULTILEVEL_FIELDS)

        self.assertListEqual(local, [])
        self.assertDictEqual(related, {
            "accounts": (
                "number",
                "owner",
                ("payments", (
                    "value",
                    "date"
                ))
            )
        })

    def test_filter_local_fields_1(self):
        local = ("a", "b", "c")
        other = [PurposeSplitFields(("a",)), PurposeSplitFields(("a", "b")), PurposeSplitFields(("b",))]

        out = self.purpose.filter_local_fields(local, other)

        self.assertListEqual(out, ["c"])

    def test_filter_local_fields_2(self):
        local = ("a", "b", "c")
        other = [PurposeSplitFields(("a", "b"))]

        out = self.purpose.filter_local_fields(local, other)

        self.assertListEqual(out, ["c"])

    def test_filter_local_fields_3(self):
        local = ("a", "b", "c")
        other = [PurposeSplitFields(("d", "e", "f"))]

        out = self.purpose.filter_local_fields(local, other)

        self.assertListEqual(out, ["a", "b", "c"])

    def test_filter_related_fields_no_recursion(self):
        related = {"emails": ("email",)}
        others = [PurposeSplitFields(related={"accounts": ("number",)})]

        out = self.purpose.filter_related_fields(related, others, Customer)

        self.assertTupleEqual(out, (("emails", ("email",)),))

    @mock.patch.object(AbstractPurpose, "get_filtered_fields")
    def test_filter_related_fields(self, get_filtered_fields_mock):
        related = {"emails": ("email",)}
        others = [PurposeSplitFields(related={"emails": ("email",)}),
                  PurposeSplitFields(related={"accounts": ("number",)})]
        get_filtered_fields_mock.return_value.__len__ = lambda _: 1  # Avoid being filtered out

        out = self.purpose.filter_related_fields(related, others, Customer)

        get_filtered_fields_mock.assert_called_with(Email, ("email",), [("email",)])

        self.assertTupleEqual(out, (("emails", get_filtered_fields_mock.return_value),))

    @mock.patch.object(AbstractPurpose, "get_filtered_fields")
    def test_filter_related_fields_2(self, get_filtered_fields_mock):
        related = {"emails": ("email",)}
        others = [PurposeSplitFields(related={"emails": ("email",)}),
                  PurposeSplitFields(related={"emails": ("email",)})]
        get_filtered_fields_mock.return_value.__len__ = lambda _: 1  # Avoid being filtered out

        out = self.purpose.filter_related_fields(related, others, Customer)

        get_filtered_fields_mock.assert_called_with(Email, ("email",), [("email",), ("email",)])

        self.assertTupleEqual(out, (("emails", get_filtered_fields_mock.return_value),))

    @mock.patch.object(AbstractPurpose, "get_filtered_fields")
    def test_filter_related_fields_3(self, get_filtered_fields_mock):
        related = {"emails": ("email",), "accounts": ("number",)}
        others = [PurposeSplitFields(related={"emails": ("email",)}),
                  PurposeSplitFields(related={"emails": ("email",)})]
        get_filtered_fields_mock.return_value.__len__ = lambda _: 1  # Avoid being filtered out

        out = self.purpose.filter_related_fields(related, others, Customer)

        get_filtered_fields_mock.assert_called_with(Email, ("email",), [("email",), ("email",)])

        self.assertTupleEqual(out, (("emails", get_filtered_fields_mock.return_value), ("accounts", ("number",))))

    def test_get_filtered_fields(self):
        others = [PurposeSplitFields(related={"emails": ("email",)}).get_tuple()]

        out = self.purpose.get_filtered_fields(Customer, BASIC_FIELDS, others)

        self.assertTupleEqual(out, ('primary_email_address',))

    def test_get_filtered_fields_2(self):
        others = [PurposeSplitFields(('primary_email_address',), {"emails": ("email",)}).get_tuple()]

        out = self.purpose.get_filtered_fields(Customer, BASIC_FIELDS, others)

        self.assertTupleEqual(out, tuple())

    def test_get_filtered_fields_3(self):
        others = [PurposeSplitFields(('primary_email_address',), {"emails": ("email",)}).get_tuple()]

        out = self.purpose.get_filtered_fields(Customer, MULTILEVEL_FIELDS, others)

        self.assertTupleEqual(out, MULTILEVEL_FIELDS)

    def test_get_filtered_fields_4(self):
        others = [PurposeSplitFields(('primary_email_address',), {"emails": ("email",)}).get_tuple()]

        out = self.purpose.get_filtered_fields(Customer, MULTILEVEL_FIELDS, others)

        self.assertTupleEqual(out, MULTILEVEL_FIELDS)

    def test_get_filtered_fields_5(self):
        others = [
            PurposeSplitFields(('primary_email_address',), {"emails": ("email",)}),
            PurposeSplitFields(('first_name', 'phone_number')),
            PurposeSplitFields(related={"accounts": PurposeSplitFields(related={"payments": ('date',)}).get_tuple()}),
        ]
        others = [i.get_tuple() for i in others]

        out = self.purpose.get_filtered_fields(Customer, ALL_FIELDS, others)
        out_match = (
            'last_name', 'full_name', 'birth_date', 'personal_id', 'fb_id', 'last_login_ip',
            ('addresses', '__ALL__'),
            ('accounts', (
                'number', 'owner', (
                    'payments', (
                        'value',
                    )
                )
            ))
        )

        self.assertTupleEqual(out, out_match)
