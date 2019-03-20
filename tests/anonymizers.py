from gdpr import anonymizers
from gdpr.anonymizers.local import cs
from tests.models import Account, Address, ContactForm, Customer, Email, Note, Payment, Avatar, ChildE


class CustomerAnonymizer(anonymizers.ModelAnonymizer):
    first_name = anonymizers.MD5TextFieldAnonymizer()
    last_name = anonymizers.MD5TextFieldAnonymizer()
    primary_email_address = anonymizers.EmailFieldAnonymizer()

    full_name = anonymizers.CharFieldAnonymizer()
    birth_date = anonymizers.DateFieldAnonymizer()
    personal_id = cs.CzechPersonalIDSmartFieldAnonymizer()
    phone_number = cs.CzechPhoneNumberFieldAnonymizer()
    facebook_id = anonymizers.CharFieldAnonymizer()
    last_login_ip = anonymizers.IPAddressFieldAnonymizer()

    notes = anonymizers.ReverseGenericRelationAnonymizer('tests', 'Note')

    def get_encryption_key(self, obj: Customer):
        return (f"{(obj.first_name or '').strip()}::{(obj.last_name or '').strip()}::"
                f"{(obj.primary_email_address or '').strip()}")

    class Meta:
        model = Customer


class EmailAnonymizer(anonymizers.ModelAnonymizer):
    email = anonymizers.EmailFieldAnonymizer()

    class Meta:
        model = Email


class AddressAnonymizer(anonymizers.ModelAnonymizer):
    street = anonymizers.CharFieldAnonymizer()

    class Meta:
        model = Address


class AccountAnonymizer(anonymizers.ModelAnonymizer):
    number = cs.CzechAccountNumberFieldAnonymizer(use_smart_method=True)
    IBAN = cs.CzechIBANSmartFieldAnonymizer()
    owner = anonymizers.CharFieldAnonymizer()

    class Meta:
        model = Account


class PaymentAnonymizer(anonymizers.ModelAnonymizer):
    value = anonymizers.DecimalFieldAnonymizer()
    date = anonymizers.DateFieldAnonymizer()

    class Meta:
        model = Payment


class ContactFormAnonymizer(anonymizers.ModelAnonymizer):
    email = anonymizers.EmailFieldAnonymizer()
    full_name = anonymizers.CharFieldAnonymizer()

    class Meta:
        model = ContactForm
        reversible_anonymization = False


class NoteAnonymizer(anonymizers.ModelAnonymizer):
    note = anonymizers.CharFieldAnonymizer()
    contact_form = anonymizers.GenericRelationAnonymizer('tests', 'ContactForm')

    class Meta:
        model = Note


class AvatarAnonymizer(anonymizers.ModelAnonymizer):
    image = anonymizers.ReplaceFileFieldAnonymizer()

    class Meta:
        model = Avatar


class ChildEAnonymizer(anonymizers.ModelAnonymizer):
    name = anonymizers.CharFieldAnonymizer()
    first_name = anonymizers.CharFieldAnonymizer()
    last_name = anonymizers.CharFieldAnonymizer()
    birth_date = anonymizers.DateFieldAnonymizer()
    note = anonymizers.CharFieldAnonymizer()

    class Meta:
        model = ChildE
        anonymize_reversion = True
