from dateutil.relativedelta import relativedelta

from gdpr.purposes.default import AbstractPurpose

from .models import Customer


# SLUG can be any length up to 100 characters
FIRST_AND_LAST_NAME_SLUG = "FNL"
EMAIL_SLUG = "EML"
PAYMENT_VALUE_SLUG = "PVL"
ACCOUNT_SLUG = "ACC"
ACCOUNT_AND_PAYMENT_SLUG = "ACP"
ADDRESS_SLUG = "ADD"
CONTACT_FORM_SLUG = "CTF"
EVERYTHING_SLUG = "EVR"
MARKETING_SLUG = "MKT"
FACEBOOK_SLUG = "FACEBOOK"


class FirstNLastNamePurpose(AbstractPurpose):
    """Store First & Last name for 10 years."""
    name = "retain due to internet archive"
    slug = FIRST_AND_LAST_NAME_SLUG
    expiration_timedelta = relativedelta(years=10)
    fields = ("first_name", "last_name")


class EmailsPurpose(AbstractPurpose):
    """Store emails for 5 years."""
    name = "retain due to over cat overlords"
    slug = EMAIL_SLUG
    expiration_timedelta = relativedelta(years=5)
    fields = (
        ("emails", (
            "email",
        )),
        ("other_registrations", (
            'email_address',
        )),
        ("last_registration", (
            'email_address',
        )),
    )


class PaymentValuePurpose(AbstractPurpose):
    name = "retain due to Foo bar"
    slug = PAYMENT_VALUE_SLUG
    expiration_timedelta = relativedelta(months=6)
    fields = (
        ("accounts", (
            ("payments", (
                "value",
            )),
        )),
    )


class AccountPurpose(AbstractPurpose):
    name = "retain due to Lorem ipsum"
    slug = ACCOUNT_SLUG
    expiration_timedelta = relativedelta(years=2)
    fields = (
        ("accounts", (
            "number",
            "owner"
        )),
    )


class AccountsAndPaymentsPurpose(AbstractPurpose):
    name = "retain due to Gandalf"
    slug = ACCOUNT_AND_PAYMENT_SLUG
    expiration_timedelta = relativedelta(years=3)
    fields = (
        ("accounts", (
            "number",
            "owner",
            ("payments", (
                "value",
                "date"
            )),
        )),
    )


class AddressPurpose(AbstractPurpose):
    name = "retain due to why not?"
    slug = ADDRESS_SLUG
    expiration_timedelta = relativedelta(years=1)
    fields = (
        ("addresses", (
            "street",
            "house_number"
        )),
    )


class EverythingPurpose(AbstractPurpose):
    name = "retain due to Area 51"
    slug = EVERYTHING_SLUG
    expiration_timedelta = relativedelta(years=51)
    fields = (
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


class ContactFormPurpose(AbstractPurpose):
    name = "retain due to mailing campaign"
    slug = CONTACT_FORM_SLUG
    expiration_timedelta = relativedelta(months=1)
    fields = "__ALL__"


class MarketingPurpose(AbstractPurpose):
    """retain due customers wanting more adds"""
    name = "retain due customers wanting more adds"
    slug = MARKETING_SLUG
    expiration_timedelta = relativedelta(years=1)
    fields = ()
    source_model_class = Customer


class FacebookPurpose(AbstractPurpose):
    name = "retain due to facebook ID"
    slug = FACEBOOK_SLUG
    expiration_timedelta = relativedelta(years=5)
    fields = "__ALL__"

    source_model_class = 'tests.Customer'

    def can_anonymize_obj(self, obj, fields):
        return obj.facebook_id is not None
