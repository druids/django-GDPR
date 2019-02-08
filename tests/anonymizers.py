from gdpr import anonymizers
from tests.models import Account, Address, ContactForm, Customer, Email, Payment, Note


class CustomerAnonymizer(anonymizers.ModelAnonymizer):
    first_name = anonymizers.MD5TextFieldAnonymizer()
    last_name = anonymizers.MD5TextFieldAnonymizer()
    primary_email_address = anonymizers.EmailFieldAnonymizer()

    full_name = anonymizers.NameFieldAnonymizer()
    birth_date = anonymizers.DateFieldAnonymizer()
    personal_id = anonymizers.PersonalIIDFieldAnonymizer()
    phone_number = anonymizers.PhoneFieldAnonymizer()
    fb_id = anonymizers.CharFieldAnonymizer()
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
    number = anonymizers.AccountNumberFieldAnonymizer()
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
    full_name = anonymizers.NameFieldAnonymizer()

    class Meta:
        model = ContactForm
        reversible_anonymization = False


class NoteAnonymizer(anonymizers.ModelAnonymizer):
    note = anonymizers.CharFieldAnonymizer()
    contact_form = anonymizers.GenericRelationAnonymizer('tests', 'ContactForm')

    class Meta:
        model = Note
