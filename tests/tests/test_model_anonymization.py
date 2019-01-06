from django.test import TestCase

from tests.models import Account, Address, ContactForm, Customer, Email, Payment
from .data import *
from .utils import NotImplementedMixin


class TestModelAnonymization(NotImplementedMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer: Customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()

    def test_anonymize_customer(self):
        self.customer.anonymize_obj()
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertNotEqual(anon_customer.full_name, "%s %s" % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME))
        self.assertNotEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertNotEqual(anon_customer.personal_id, CUSTOMER__PERSONAL_ID)
        self.assertNotEqual(anon_customer.phone_number, CUSTOMER__PHONE_NUMBER)
        self.assertNotImplementedNotEqual(anon_customer.birth_date, CUSTOMER__BIRTH_DATE)
        self.assertNotImplementedNotEqual(anon_customer.fb_id, CUSTOMER__FB_ID)
        self.assertNotImplementedNotEqual(str(anon_customer.last_login_ip), CUSTOMER__IP)

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

        self.assertNotImplementedNotEqual(anon_address.street, ADDRESS__STREET)
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

        self.assertNotImplementedNotEqual(anon_account.number, ACCOUNT__NUMBER)
        self.assertNotEqual(anon_account.owner, ACCOUNT__OWNER)

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

        self.assertNotImplementedNotEqual(anon_payment.value, PAYMENT__VALUE)
        self.assertNotImplementedNotEqual(anon_payment.date, self.payment.date)

    def test_contact_form(self):
        self.contact_form: ContactForm = ContactForm(
            email=CUSTOMER__EMAIL,
            full_name="%s %s" % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME)
        )
        self.contact_form.save()
        self.contact_form.anonymize_obj()

        anon_contact_form: ContactForm = ContactForm.objects.get(pk=self.contact_form.pk)

        self.assertNotEqual(anon_contact_form.email, CUSTOMER__EMAIL)
        self.assertNotEqual(anon_contact_form.full_name, self.contact_form.full_name)
