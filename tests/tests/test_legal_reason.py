from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from faker import Faker

from gdpr.models import LegalReason
from tests.models import Account, Customer, Email, Payment
from tests.purposes import ACCOUNT_N_PAYMENT_SLUG, EMAIL_SLUG, FIRST_N_LAST_NAME_SLUG
from tests.tests.data import (
    ACCOUNT__NUMBER, ACCOUNT__NUMBER2, ACCOUNT__OWNER, ACCOUNT__OWNER2, CUSTOMER__EMAIL, CUSTOMER__EMAIL2,
    CUSTOMER__EMAIL3, CUSTOMER__FIRST_NAME, CUSTOMER__KWARGS, CUSTOMER__LAST_NAME)
from tests.tests.utils import AnonymizedDataMixin, NotImplementedMixin


class TestLegalReason(AnonymizedDataMixin, NotImplementedMixin, TestCase):
    def setUp(self):
        self.fake = Faker()

    @classmethod
    def setUpTestData(cls):
        cls.customer: Customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()

    def test_create_legal_reson_from_slug(self):
        LegalReason.objects.create_consent(FIRST_N_LAST_NAME_SLUG, self.customer).save()

        self.assertTrue(LegalReason.objects.filter(
            purpose_slug=FIRST_N_LAST_NAME_SLUG, source_object_id=self.customer.pk,
            source_object_content_type=ContentType.objects.get_for_model(Customer)).exists())

    def test_expirement_legal_reason(self):
        legal = LegalReason.objects.create_consent(FIRST_N_LAST_NAME_SLUG, self.customer)
        legal.expire()

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "last_name")
        # make sure only data we want were anonymized
        self.assertEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_customer, "primary_email_address")

    def test_expirement_legal_reason_related(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        related_email2: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL2)
        related_email2.save()

        related_email3: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL3)
        related_email3.save()

        legal = LegalReason.objects.create_consent(EMAIL_SLUG, self.customer)
        legal.expire()

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_customer, "primary_email_address")

        # make sure only data we want were anonymized
        self.assertEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, "first_name")

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        self.assertNotEqual(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, "email")

        anon_related_email2: Email = Email.objects.get(pk=related_email2.pk)

        self.assertNotEqual(anon_related_email2.email, CUSTOMER__EMAIL2)
        self.assertAnonymizedDataExists(anon_related_email2, "email")

        anon_related_email3: Email = Email.objects.get(pk=related_email3.pk)

        self.assertNotEqual(anon_related_email3.email, CUSTOMER__EMAIL3)
        self.assertAnonymizedDataExists(anon_related_email3, "email")

    def test_expirement_legal_reason_two_level_related(self):
        account_1: Account = Account(customer=self.customer, number=ACCOUNT__NUMBER, owner=ACCOUNT__OWNER)
        account_1.save()
        account_2: Account = Account(customer=self.customer, number=ACCOUNT__NUMBER2, owner=ACCOUNT__OWNER2)
        account_2.save()

        payment_1: Payment = Payment(account=account_1,
                                     value=self.fake.pydecimal(left_digits=8, right_digits=2, positive=True))
        payment_1.save()
        payment_2: Payment = Payment(account=account_1,
                                     value=self.fake.pydecimal(left_digits=8, right_digits=2, positive=True))
        payment_2.save()

        payment_3: Payment = Payment(account=account_2,
                                     value=self.fake.pydecimal(left_digits=8, right_digits=2, positive=True))
        payment_3.save()
        payment_4: Payment = Payment(account=account_2,
                                     value=self.fake.pydecimal(left_digits=8, right_digits=2, positive=True))
        payment_4.save()

        legal = LegalReason.objects.create_consent(ACCOUNT_N_PAYMENT_SLUG, self.customer)
        legal.expire()

        anon_account_1: Account = Account.objects.get(pk=account_1.pk)

        self.assertNotEqual(anon_account_1.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataExists(anon_account_1, "number")
        self.assertNotEqual(anon_account_1.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataExists(anon_account_1, "owner")

        anon_account_2: Account = Account.objects.get(pk=account_2.pk)

        self.assertNotEqual(anon_account_2.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataExists(anon_account_2, "number")
        self.assertNotEqual(anon_account_2.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataExists(anon_account_2, "owner")

        for payment in [payment_1, payment_2, payment_3, payment_4]:
            anon_payment: Payment = Payment.objects.get(pk=payment.pk)

            self.assertNotEqual(anon_payment.value, payment.value)
            self.assertAnonymizedDataExists(anon_payment, "value")
            self.assertNotEqual(anon_payment.date, payment.date)
            self.assertAnonymizedDataExists(anon_payment, "date")
