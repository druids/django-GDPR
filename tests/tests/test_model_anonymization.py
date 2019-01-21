from django.test import TestCase

from tests.models import Account, Address, ContactForm, Customer, Email, Payment
from .data import (
    ACCOUNT__NUMBER, ACCOUNT__OWNER, ADDRESS__CITY, ADDRESS__HOUSE_NUMBER, ADDRESS__POST_CODE, ADDRESS__STREET,
    CUSTOMER__BIRTH_DATE, CUSTOMER__EMAIL, CUSTOMER__FB_ID, CUSTOMER__FIRST_NAME, CUSTOMER__IP, CUSTOMER__KWARGS,
    CUSTOMER__LAST_NAME, CUSTOMER__PERSONAL_ID, CUSTOMER__PHONE_NUMBER, PAYMENT__VALUE)
from .utils import AnonymizedDataMixin, NotImplementedMixin


class TestModelAnonymization(AnonymizedDataMixin, NotImplementedMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer: Customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()

    def test_anonymize_customer(self):
        self.customer.anonymize_obj()
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "last_name")
        self.assertNotEqual(anon_customer.full_name, "%s %s" % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME))
        self.assertAnonymizedDataExists(anon_customer, "full_name")
        self.assertNotEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_customer, "primary_email_address")
        self.assertNotEqual(anon_customer.personal_id, CUSTOMER__PERSONAL_ID)
        self.assertAnonymizedDataExists(anon_customer, "personal_id")
        self.assertNotEqual(anon_customer.phone_number, CUSTOMER__PHONE_NUMBER)
        self.assertAnonymizedDataExists(anon_customer, "phone_number")
        self.assertNotEquals(anon_customer.birth_date, CUSTOMER__BIRTH_DATE)
        self.assertAnonymizedDataExists(anon_customer, "first_name")
        self.assertNotEquals(anon_customer.fb_id, CUSTOMER__FB_ID)
        self.assertAnonymizedDataExists(anon_customer, "first_name")
        self.assertNotImplementedNotEqual(str(anon_customer.last_login_ip), CUSTOMER__IP)
        self.assertAnonymizedDataExists(anon_customer, "first_name")

    def test_email(self):
        self.email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        self.email.save()
        self.email.anonymize_obj()
        anon_email: Email = Email.objects.get(pk=self.email.pk)

        self.assertNotEqual(anon_email.email, CUSTOMER__EMAIL)

    def test_address(self):
        self.address: Address = Address(
            customer=self.customer,
            street=ADDRESS__STREET,
            house_number=ADDRESS__HOUSE_NUMBER,
            city=ADDRESS__CITY,
            post_code=ADDRESS__POST_CODE,
        )
        self.address.save()
        self.address.anonymize_obj()
        anon_address: Address = Address.objects.get(pk=self.address.pk)

        self.assertNotEqual(anon_address.street, ADDRESS__STREET)
        self.assertAnonymizedDataExists(anon_address, "street")
        self.assertEqual(anon_address.house_number, ADDRESS__HOUSE_NUMBER)
        self.assertEqual(anon_address.city, ADDRESS__CITY)
        self.assertEqual(anon_address.post_code, ADDRESS__POST_CODE)

    def test_account(self):
        self.account: Account = Account(
            customer=self.customer,
            number=ACCOUNT__NUMBER,
            owner=ACCOUNT__OWNER
        )
        self.account.save()
        self.account.anonymize_obj()

        anon_account: Account = Account.objects.get(pk=self.account.pk)

        self.assertNotEqual(anon_account.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataExists(anon_account, "number")
        self.assertNotEqual(anon_account.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataExists(anon_account, "owner")

    def test_payment(self):
        self.account: Account = Account(
            customer=self.customer,
            number=ACCOUNT__NUMBER,
            owner=ACCOUNT__OWNER
        )
        self.account.save()
        self.payment: Payment = Payment(
            account=self.account,
            value=PAYMENT__VALUE,
        )
        self.payment.save()
        self.payment.anonymize_obj()

        anon_payment: Payment = Payment.objects.get(pk=self.payment.pk)

        self.assertNotEquals(anon_payment.value, PAYMENT__VALUE)
        self.assertAnonymizedDataExists(anon_payment, "value")
        self.assertNotEquals(anon_payment.date, self.payment.date)
        self.assertAnonymizedDataExists(anon_payment, "date")

    def test_contact_form(self):
        self.contact_form: ContactForm = ContactForm(
            email=CUSTOMER__EMAIL,
            full_name="%s %s" % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME)
        )
        self.contact_form.save()
        self.contact_form.anonymize_obj()

        anon_contact_form: ContactForm = ContactForm.objects.get(pk=self.contact_form.pk)

        self.assertNotEqual(anon_contact_form.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_contact_form, "email")
        self.assertNotEqual(anon_contact_form.full_name, self.contact_form.full_name)
        self.assertAnonymizedDataExists(anon_contact_form, "full_name")

    def test_anonymization_of_anonymized_data(self):
        """Test that anonymized data are not anonymized again."""
        self.customer.anonymize_obj()
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")

        anon_customer.anonymize_obj()
        anon_customer2: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertEqual(anon_customer2.first_name, anon_customer.first_name)
        self.assertNotEqual(anon_customer2.first_name, CUSTOMER__FIRST_NAME)

    def test_anonymization_field_matrix(self):
        self.customer.anonymize_obj(fields=("first_name",))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, "last_name")

    def test_anonymization_field_matrix_related(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        self.customer.anonymize_obj(fields=("first_name", ("emails", ("email",))))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, "last_name")

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        self.assertNotEqual(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, "email")

    def test_anonymization_field_matrix_related_all(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        self.customer.anonymize_obj(fields=("first_name", ("emails", "__ALL__")))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, "last_name")

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        self.assertNotEqual(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, "email")
