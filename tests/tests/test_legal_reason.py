from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from faker import Faker
from gdpr.models import LegalReason
from germanium.tools import assert_equal, assert_not_equal, assert_true, assert_raises
from tests.models import Account, Customer, Email, Payment
from tests.purposes import (
    ACCOUNT_AND_PAYMENT_SLUG, ACCOUNT_SLUG, EMAIL_SLUG, EVERYTHING_SLUG, FACEBOOK_SLUG, FIRST_AND_LAST_NAME_SLUG,
    EmailsPurpose, FacebookPurpose, MarketingPurpose
)
from tests.tests.data import (
    ACCOUNT__NUMBER, ACCOUNT__NUMBER2, ACCOUNT__OWNER, ACCOUNT__OWNER2, CUSTOMER__BIRTH_DATE, CUSTOMER__EMAIL,
    CUSTOMER__EMAIL2, CUSTOMER__EMAIL3, CUSTOMER__FACEBOOK_ID, CUSTOMER__FIRST_NAME, CUSTOMER__IP, CUSTOMER__KWARGS,
    CUSTOMER__LAST_NAME, CUSTOMER__PERSONAL_ID, CUSTOMER__PHONE_NUMBER
)
from tests.tests.utils import AnonymizedDataMixin, NotImplementedMixin


class TestLegalReason(AnonymizedDataMixin, NotImplementedMixin, TestCase):

    def setUp(self):
        self.fake = Faker()

    @classmethod
    def setUpTestData(cls):
        cls.customer: Customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()

    def test_create_legal_reson_from_slug(self):
        LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer).save()

        assert_true(LegalReason.objects.filter(
            purpose_slug=FIRST_AND_LAST_NAME_SLUG, source_object_id=self.customer.pk,
            source_object_content_type=ContentType.objects.get_for_model(Customer)).exists())

    def test_expirement_legal_reason(self):
        legal = LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer)
        legal.expire()

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")
        assert_not_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "last_name")
        # make sure only data we want were anonymized
        assert_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_customer, "primary_email_address")

    def test_renew_legal_reason(self):
        legal = LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer)
        legal.expire()
        legal.renew()

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        # Non reversible anonymization
        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "first_name")
        assert_not_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, "last_name")

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

        assert_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_customer, "primary_email_address")

        # make sure only data we want were anonymized
        assert_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, "first_name")

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        assert_not_equal(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, "email")

        anon_related_email2: Email = Email.objects.get(pk=related_email2.pk)

        assert_not_equal(anon_related_email2.email, CUSTOMER__EMAIL2)
        self.assertAnonymizedDataExists(anon_related_email2, "email")

        anon_related_email3: Email = Email.objects.get(pk=related_email3.pk)

        assert_not_equal(anon_related_email3.email, CUSTOMER__EMAIL3)
        self.assertAnonymizedDataExists(anon_related_email3, "email")

    def test_renew_legal_reason_related(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        related_email2: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL2)
        related_email2.save()

        related_email3: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL3)
        related_email3.save()

        legal = LegalReason.objects.create_consent(EMAIL_SLUG, self.customer)
        legal.expire()

        anon_legal = LegalReason.objects.get(pk=legal.pk)
        anon_legal.renew()

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        assert_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_customer, "primary_email_address")

        # make sure only data we want were anonymized
        assert_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, "first_name")

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        assert_equal(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_related_email, "email")

        anon_related_email2: Email = Email.objects.get(pk=related_email2.pk)

        assert_equal(anon_related_email2.email, CUSTOMER__EMAIL2)
        self.assertAnonymizedDataNotExists(anon_related_email2, "email")

        anon_related_email3: Email = Email.objects.get(pk=related_email3.pk)

        assert_equal(anon_related_email3.email, CUSTOMER__EMAIL3)
        self.assertAnonymizedDataNotExists(anon_related_email3, "email")

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

        legal = LegalReason.objects.create_consent(ACCOUNT_AND_PAYMENT_SLUG, self.customer)
        legal.expire()

        anon_account_1: Account = Account.objects.get(pk=account_1.pk)

        assert_not_equal(anon_account_1.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataExists(anon_account_1, "number")
        assert_not_equal(anon_account_1.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataExists(anon_account_1, "owner")

        anon_account_2: Account = Account.objects.get(pk=account_2.pk)

        assert_not_equal(anon_account_2.number, ACCOUNT__NUMBER2)
        self.assertAnonymizedDataExists(anon_account_2, "number")
        assert_not_equal(anon_account_2.owner, ACCOUNT__OWNER2)
        self.assertAnonymizedDataExists(anon_account_2, "owner")

        for payment in [payment_1, payment_2, payment_3, payment_4]:
            anon_payment: Payment = Payment.objects.get(pk=payment.pk)

            assert_not_equal(anon_payment.value, payment.value)
            self.assertAnonymizedDataExists(anon_payment, "value")
            assert_not_equal(anon_payment.date, payment.date)
            self.assertAnonymizedDataExists(anon_payment, "date")

    def test_renew_legal_reason_two_level_related(self):
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

        legal = LegalReason.objects.create_consent(ACCOUNT_AND_PAYMENT_SLUG, self.customer)
        legal.expire()

        anon_legal = LegalReason.objects.get(pk=legal.pk)
        anon_legal.renew()

        anon_account_1: Account = Account.objects.get(pk=account_1.pk)

        assert_equal(anon_account_1.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataNotExists(anon_account_1, "number")
        assert_equal(anon_account_1.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataNotExists(anon_account_1, "owner")

        anon_account_2: Account = Account.objects.get(pk=account_2.pk)

        assert_equal(anon_account_2.number, ACCOUNT__NUMBER2)
        self.assertAnonymizedDataNotExists(anon_account_2, "number")
        assert_equal(anon_account_2.owner, ACCOUNT__OWNER2)
        self.assertAnonymizedDataNotExists(anon_account_2, "owner")

        for payment in [payment_1, payment_2, payment_3, payment_4]:
            anon_payment: Payment = Payment.objects.get(pk=payment.pk)

            assert_equal(anon_payment.value, payment.value)
            self.assertAnonymizedDataNotExists(anon_payment, "value")
            assert_equal(anon_payment.date, payment.date)
            self.assertAnonymizedDataNotExists(anon_payment, "date")

    def test_email_purpose(self):
        LegalReason.objects.create_consent(EMAIL_SLUG, self.customer)

        EmailsPurpose().anonymize_obj(obj=self.customer, fields=("primary_email_address",))

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        assert_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(self.customer, 'primary_email_address')

    def test_email_purpose_related(self):
        LegalReason.objects.create_consent(EMAIL_SLUG, self.customer)

        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        EmailsPurpose().anonymize_obj(obj=self.customer, fields=("primary_email_address",))

        anon_customer = Customer.objects.get(pk=self.customer.pk)

        assert_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_customer, 'primary_email_address')

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        assert_equal(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_related_email, 'email')

    def test_legal_reason_hardcore(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        related_email2: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL2)
        related_email2.save()

        account: Account = Account(customer=self.customer, number=ACCOUNT__NUMBER, owner=ACCOUNT__OWNER)
        account.save()

        payment: Payment = Payment(account=account,
                                   value=self.fake.pydecimal(left_digits=8, right_digits=2, positive=True))
        payment.save()

        LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer)
        LegalReason.objects.create_consent(EMAIL_SLUG, self.customer)
        LegalReason.objects.create_consent(ACCOUNT_SLUG, self.customer)
        legal = LegalReason.objects.create_consent(EVERYTHING_SLUG, self.customer)
        legal.expire()

        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)
        anon_related_email: Email = Email.objects.get(pk=related_email.pk)
        anon_related_email2: Email = Email.objects.get(pk=related_email2.pk)
        anon_account: Account = Account.objects.get(pk=account.pk)
        anon_payment: Payment = Payment.objects.get(pk=payment.pk)

        # Customer - partialy anonymized
        assert_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'first_name')
        assert_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')
        assert_not_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_customer, 'primary_email_address')

        assert_not_equal(anon_customer.birth_date, CUSTOMER__BIRTH_DATE)
        self.assertAnonymizedDataExists(anon_customer, 'birth_date')
        assert_not_equal(anon_customer.personal_id, CUSTOMER__PERSONAL_ID)
        self.assertAnonymizedDataExists(anon_customer, 'personal_id')
        assert_not_equal(anon_customer.phone_number, CUSTOMER__PHONE_NUMBER)
        self.assertAnonymizedDataExists(anon_customer, 'phone_number')
        assert_not_equal(anon_customer.facebook_id, CUSTOMER__FACEBOOK_ID)
        self.assertAnonymizedDataExists(anon_customer, 'facebook_id')
        assert_not_equal(anon_customer.last_login_ip, CUSTOMER__IP)
        self.assertAnonymizedDataExists(anon_customer, 'last_login_ip')

        # Email - not anonymized
        assert_equal(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataNotExists(anon_related_email, 'email')
        assert_equal(anon_related_email2.email, CUSTOMER__EMAIL2)
        self.assertAnonymizedDataNotExists(anon_related_email2, 'email')

        # Account - not anonymized
        assert_equal(anon_account.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataNotExists(anon_account, "number")
        assert_equal(anon_account.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataNotExists(anon_account, "owner")

        # Payment - fully anonymized
        assert_not_equal(anon_payment.value, payment.value)
        self.assertAnonymizedDataExists(anon_payment, "value")
        assert_not_equal(anon_payment.date, payment.date)
        self.assertAnonymizedDataExists(anon_payment, "date")

    def test_purpose_source_model_class_should_be_set_with_string(self):
        assert_equal(FacebookPurpose.source_model_class, Customer)

    def test_purpose_source_model_class_should_be_set_directly(self):
        assert_equal(MarketingPurpose.source_model_class, Customer)

    def test_purpose_should_be_set_only_to_the_right_source_model(self):
        LegalReason.objects.create_consent(FACEBOOK_SLUG, self.customer)
        with assert_raises(KeyError):
            LegalReason.objects.create_consent(FACEBOOK_SLUG, Email(customer=self.customer, email=CUSTOMER__EMAIL))

    def test_facebook_purpose_should_anonymize_customer_with_facebook_id(self):
        customer = Customer.objects.get(pk=self.customer.pk)
        legal_reason = LegalReason.objects.create_consent(FACEBOOK_SLUG, customer)
        legal_reason.save()
        legal_reason.expire()
        customer.refresh_from_db()
        assert_not_equal(customer.first_name, CUSTOMER__FIRST_NAME)

    def test_facebook_purpose_should_anonymize_customer_without_facebook_id(self):
        customer = Customer.objects.get(pk=self.customer.pk)
        legal_reason = LegalReason.objects.create_consent(FACEBOOK_SLUG, customer)
        customer.facebook_id = None
        customer.save()
        legal_reason.save()
        legal_reason.expire()
        customer.refresh_from_db()
        assert_equal(customer.first_name, CUSTOMER__FIRST_NAME)
