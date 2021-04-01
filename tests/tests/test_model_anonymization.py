from datetime import timedelta
from typing import List
from unittest import skipIf

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase

from gdpr.anonymizers import ModelAnonymizer
from gdpr.loading import anonymizer_register
from gdpr.utils import get_reversion_local_field_dict, is_reversion_installed
from germanium.tools import assert_dict_equal, assert_equal, assert_not_equal, assert_raises
from tests.anonymizers import ChildEAnonymizer, ContactFormAnonymizer
from tests.models import Account, Address, Avatar, ChildE, ContactForm, Customer, Email, Note, Payment

from .data import (
    ACCOUNT__IBAN, ACCOUNT__NUMBER, ACCOUNT__OWNER, ACCOUNT__SWIFT, ADDRESS__CITY, ADDRESS__HOUSE_NUMBER,
    ADDRESS__POST_CODE, ADDRESS__STREET, CUSTOMER__BIRTH_DATE, CUSTOMER__EMAIL, CUSTOMER__EMAIL2, CUSTOMER__EMAIL3,
    CUSTOMER__FACEBOOK_ID, CUSTOMER__FIRST_NAME, CUSTOMER__IP, CUSTOMER__KWARGS, CUSTOMER__LAST_NAME,
    CUSTOMER__PERSONAL_ID, CUSTOMER__PHONE_NUMBER, PAYMENT__VALUE
)
from .utils import AnonymizedDataMixin, NotImplementedMixin


class TestModelAnonymization(AnonymizedDataMixin, NotImplementedMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer: Customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()
        cls.base_encryption_key = 'LoremIpsum'

    def test_anonymize_customer(self):
        self.customer._anonymize_obj()
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')
        assert_not_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'last_name')
        assert_not_equal(anon_customer.full_name, '%s %s' % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME))
        self.assertAnonymizedDataExists(anon_customer, 'full_name')
        assert_not_equal(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_customer, 'primary_email_address')
        assert_not_equal(anon_customer.personal_id, CUSTOMER__PERSONAL_ID)
        self.assertAnonymizedDataExists(anon_customer, 'personal_id')
        assert_not_equal(anon_customer.phone_number, CUSTOMER__PHONE_NUMBER)
        self.assertAnonymizedDataExists(anon_customer, 'phone_number')
        assert_not_equal(anon_customer.birth_date, CUSTOMER__BIRTH_DATE)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')
        assert_not_equal(anon_customer.facebook_id, CUSTOMER__FACEBOOK_ID)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')
        assert_not_equal(str(anon_customer.last_login_ip), CUSTOMER__IP)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

    def test_email(self):
        self.email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        self.email.save()
        self.email._anonymize_obj(base_encryption_key=self.base_encryption_key)
        anon_email: Email = Email.objects.get(pk=self.email.pk)

        assert_not_equal(anon_email.email, CUSTOMER__EMAIL)

    def test_address(self):
        self.address: Address = Address(
            customer=self.customer,
            street=ADDRESS__STREET,
            house_number=ADDRESS__HOUSE_NUMBER,
            city=ADDRESS__CITY,
            post_code=ADDRESS__POST_CODE,
        )
        self.address.save()
        self.address._anonymize_obj(base_encryption_key=self.base_encryption_key)
        anon_address: Address = Address.objects.get(pk=self.address.pk)

        assert_not_equal(anon_address.street, ADDRESS__STREET)
        self.assertAnonymizedDataExists(anon_address, 'street')
        assert_equal(anon_address.house_number, ADDRESS__HOUSE_NUMBER)
        assert_equal(anon_address.city, ADDRESS__CITY)
        assert_equal(anon_address.post_code, ADDRESS__POST_CODE)

    def test_account(self):
        self.account: Account = Account(
            customer=self.customer,
            number=ACCOUNT__NUMBER,
            owner=ACCOUNT__OWNER,
            IBAN=ACCOUNT__IBAN,
            swift=ACCOUNT__SWIFT,
        )
        self.account.save()
        self.account._anonymize_obj(base_encryption_key=self.base_encryption_key)

        anon_account: Account = Account.objects.get(pk=self.account.pk)

        assert_not_equal(anon_account.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataExists(anon_account, 'number')
        assert_not_equal(anon_account.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataExists(anon_account, 'owner')
        assert_not_equal(anon_account.IBAN, ACCOUNT__IBAN)
        self.assertAnonymizedDataExists(anon_account, 'IBAN')

    def test_payment(self):
        self.account: Account = Account(
            customer=self.customer,
            number=ACCOUNT__NUMBER,
            owner=ACCOUNT__OWNER,
            IBAN=ACCOUNT__IBAN,
            swift=ACCOUNT__SWIFT,
        )
        self.account.save()
        self.payment: Payment = Payment(
            account=self.account,
            value=PAYMENT__VALUE,
        )
        self.payment.save()
        payment_date = self.payment.date

        self.payment._anonymize_obj(base_encryption_key=self.base_encryption_key)

        anon_payment: Payment = Payment.objects.get(pk=self.payment.pk)

        assert_not_equal(anon_payment.value, PAYMENT__VALUE)
        self.assertAnonymizedDataExists(anon_payment, 'value')
        assert_not_equal(anon_payment.date, payment_date)
        self.assertAnonymizedDataExists(anon_payment, 'date')

    def test_contact_form(self):
        FULL_NAME = '%s %s' % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME)
        self.contact_form: ContactForm = ContactForm(
            email=CUSTOMER__EMAIL,
            full_name=FULL_NAME
        )
        self.contact_form.save()
        self.contact_form._anonymize_obj()

        anon_contact_form: ContactForm = ContactForm.objects.get(pk=self.contact_form.pk)

        assert_not_equal(anon_contact_form.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_contact_form, 'email')
        assert_not_equal(anon_contact_form.full_name, FULL_NAME)
        self.assertAnonymizedDataExists(anon_contact_form, 'full_name')

    def test_anonymization_of_anonymized_data(self):
        '''Test that anonymized data are not anonymized again.'''
        self.customer._anonymize_obj()
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        anon_customer._anonymize_obj()
        anon_customer2: Customer = Customer.objects.get(pk=self.customer.pk)

        assert_equal(anon_customer2.first_name, anon_customer.first_name)
        assert_not_equal(anon_customer2.first_name, CUSTOMER__FIRST_NAME)

    def test_anonymization_field_matrix(self):
        self.customer._anonymize_obj(fields=('first_name',))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        assert_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')

    def test_anonymization_field_matrix_related(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        self.customer._anonymize_obj(fields=('first_name', ('emails', ('email',))))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        assert_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        assert_not_equal(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, 'email')

    def test_anonymization_field_matrix_related_all(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        self.customer._anonymize_obj(fields=('first_name', ('emails', '__ALL__')))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        assert_not_equal(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        assert_equal(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        assert_not_equal(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, 'email')

    def test_reverse_generic_relation(self):
        note: Note = Note(note='Test message')
        note.content_object = self.customer
        note.save()

        self.customer._anonymize_obj(fields=(('notes', '__ALL__'),))

        anon_note: Note = Note.objects.get(pk=note.pk)

        assert_not_equal(anon_note.note, note.note)
        self.assertAnonymizedDataExists(note, 'note')

        self.customer._deanonymize_obj(fields=(('notes', '__ALL__'),))

        anon_note2: Note = Note.objects.get(pk=note.pk)

        assert_equal(anon_note2.note, note.note)
        self.assertAnonymizedDataNotExists(note, 'note')

    def test_irreversible_deanonymization(self):
        contact_form: ContactForm = ContactForm(email=CUSTOMER__EMAIL, full_name=CUSTOMER__LAST_NAME)
        contact_form.save()
        contact_form._anonymize_obj(fields=('__ALL__',))

        assert_raises(ModelAnonymizer.IrreversibleAnonymizerException, contact_form._deanonymize_obj,
                      fields=('__ALL__',))

    def test_generic_relation_anonymizer(self):
        contact_form: ContactForm = ContactForm(email=CUSTOMER__EMAIL, full_name=CUSTOMER__LAST_NAME)
        contact_form.save()
        note: Note = Note(note='Test message')
        note.content_object = contact_form
        note.save()

        note._anonymize_obj(fields=(('contact_form', '__ALL__'),), base_encryption_key=self.base_encryption_key)

        anon_contact_form: ContactForm = ContactForm.objects.get(pk=contact_form.pk)

        assert_not_equal(anon_contact_form.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_contact_form, 'email')
        assert_not_equal(anon_contact_form.full_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_contact_form, 'full_name')

    @skipIf(not is_reversion_installed(), 'Django-reversion is not installed.')
    def test_reversion_anonymization(self):
        from reversion import revisions as reversion
        from reversion.models import Version
        from gdpr.utils import get_reversion_versions

        anon = ContactFormAnonymizer()
        anon.Meta.anonymize_reversion = True
        anon.Meta.reversible_anonymization = True

        user = User(username='test_username')
        user.save()

        with reversion.create_revision():
            form = ContactForm()
            form.email = CUSTOMER__EMAIL
            form.full_name = CUSTOMER__LAST_NAME
            form.save()

            reversion.set_user(user)

        with reversion.create_revision():
            form.email = CUSTOMER__EMAIL2
            form.save()

            reversion.set_user(user)

        with reversion.create_revision():
            form.email = CUSTOMER__EMAIL3
            form.save()

            reversion.set_user(user)

        versions: List[Version] = get_reversion_versions(form).order_by('id')

        assert_equal(versions[0].field_dict['email'], CUSTOMER__EMAIL)
        assert_equal(versions[1].field_dict['email'], CUSTOMER__EMAIL2)
        assert_equal(versions[2].field_dict['email'], CUSTOMER__EMAIL3)

        anon.anonymize_obj(form, base_encryption_key=self.base_encryption_key)

        anon_versions: List[Version] = get_reversion_versions(form).order_by('id')
        anon_form = ContactForm.objects.get(pk=form.pk)

        assert_not_equal(anon_versions[0].field_dict['email'], CUSTOMER__EMAIL)
        assert_not_equal(anon_versions[1].field_dict['email'], CUSTOMER__EMAIL2)
        assert_not_equal(anon_versions[2].field_dict['email'], CUSTOMER__EMAIL3)
        assert_not_equal(anon_form.email, CUSTOMER__EMAIL3)

        anon.deanonymize_obj(anon_form, base_encryption_key=self.base_encryption_key)

        deanon_versions: List[Version] = get_reversion_versions(form).order_by('id')
        deanon_form = ContactForm.objects.get(pk=form.pk)

        assert_equal(deanon_versions[0].field_dict['email'], CUSTOMER__EMAIL)
        assert_equal(deanon_versions[1].field_dict['email'], CUSTOMER__EMAIL2)
        assert_equal(deanon_versions[2].field_dict['email'], CUSTOMER__EMAIL3)
        assert_equal(deanon_form.email, CUSTOMER__EMAIL3)
        assert_dict_equal(versions[0].field_dict, deanon_versions[0].field_dict)
        assert_dict_equal(versions[1].field_dict, deanon_versions[1].field_dict)
        assert_dict_equal(versions[2].field_dict, deanon_versions[2].field_dict)

    @skipIf(not is_reversion_installed(), 'Django-reversion is not installed.')
    def test_reversion_anonymization_parents(self):
        from reversion import revisions as reversion
        from reversion.models import Version
        from gdpr.utils import get_reversion_versions

        anon = ChildEAnonymizer()

        user = User(username='testing_username')
        user.save()

        with reversion.create_revision():
            e = ChildE()
            e.name = 'Lorem'
            e.first_name = 'Ipsum'
            e.last_name = 'Dolor'
            e.birth_date = CUSTOMER__BIRTH_DATE
            e.note = 'sit Amet'
            e.save()

            reversion.set_user(user)

        with reversion.create_revision():
            e.name = 'LOREM'
            e.first_name = 'IPSUM'
            e.last_name = 'DOLOR'
            e.birth_date = CUSTOMER__BIRTH_DATE + timedelta(days=2)
            e.note = 'SIT AMET'
            e.save()

            reversion.set_user(user)

        versions_a: List[Version] = get_reversion_versions(e.topparenta_ptr).order_by('id')
        versions_b: List[Version] = get_reversion_versions(e.parentb_ptr).order_by('id')
        versions_c: List[Version] = get_reversion_versions(e.parentc_ptr).order_by('id')
        versions_d: List[Version] = get_reversion_versions(e.extraparentd_ptr).order_by('id')
        versions_e: List[Version] = get_reversion_versions(e).order_by('id')

        assert_equal(get_reversion_local_field_dict(versions_a[0])['name'], 'Lorem')
        assert_equal(get_reversion_local_field_dict(versions_a[1])['name'], 'LOREM')

        assert_equal(get_reversion_local_field_dict(versions_b[0])['birth_date'], CUSTOMER__BIRTH_DATE)
        assert_equal(get_reversion_local_field_dict(versions_b[1])['birth_date'],
                     CUSTOMER__BIRTH_DATE + timedelta(days=2))

        assert_equal(get_reversion_local_field_dict(versions_c[0])['first_name'], 'Ipsum')
        assert_equal(get_reversion_local_field_dict(versions_c[1])['first_name'], 'IPSUM')

        assert_equal(get_reversion_local_field_dict(versions_d[0])['note'], 'sit Amet')
        assert_equal(get_reversion_local_field_dict(versions_d[1])['note'], 'SIT AMET')

        assert_equal(get_reversion_local_field_dict(versions_e[0])['last_name'], 'Dolor')
        assert_equal(get_reversion_local_field_dict(versions_e[1])['last_name'], 'DOLOR')

        anon.anonymize_obj(e, base_encryption_key=self.base_encryption_key)

        anon_versions_a: List[Version] = get_reversion_versions(e.topparenta_ptr).order_by('id')
        anon_versions_b: List[Version] = get_reversion_versions(e.parentb_ptr).order_by('id')
        anon_versions_c: List[Version] = get_reversion_versions(e.parentc_ptr).order_by('id')
        anon_versions_d: List[Version] = get_reversion_versions(e.extraparentd_ptr).order_by('id')
        anon_versions_e: List[Version] = get_reversion_versions(e).order_by('id')
        anon_e = ChildE.objects.get(pk=e.pk)

        assert_not_equal(get_reversion_local_field_dict(anon_versions_a[0])['name'], 'Lorem')
        assert_not_equal(get_reversion_local_field_dict(anon_versions_a[1])['name'], 'LOREM')

        assert_not_equal(get_reversion_local_field_dict(anon_versions_b[0])['birth_date'], CUSTOMER__BIRTH_DATE)
        assert_not_equal(get_reversion_local_field_dict(anon_versions_b[1])['birth_date'],
                         CUSTOMER__BIRTH_DATE + timedelta(days=2))

        assert_not_equal(get_reversion_local_field_dict(anon_versions_c[0])['first_name'], 'Ipsum')
        assert_not_equal(get_reversion_local_field_dict(anon_versions_c[1])['first_name'], 'IPSUM')

        assert_not_equal(get_reversion_local_field_dict(anon_versions_d[0])['note'], 'sit Amet')
        assert_not_equal(get_reversion_local_field_dict(anon_versions_d[1])['note'], 'SIT AMET')

        assert_not_equal(get_reversion_local_field_dict(anon_versions_e[0])['last_name'], 'Dolor')
        assert_not_equal(get_reversion_local_field_dict(anon_versions_e[1])['last_name'], 'DOLOR')

        anon.deanonymize_obj(anon_e, base_encryption_key=self.base_encryption_key)

        deanon_versions_a: List[Version] = get_reversion_versions(e.topparenta_ptr).order_by('id')
        deanon_versions_b: List[Version] = get_reversion_versions(e.parentb_ptr).order_by('id')
        deanon_versions_c: List[Version] = get_reversion_versions(e.parentc_ptr).order_by('id')
        deanon_versions_d: List[Version] = get_reversion_versions(e.extraparentd_ptr).order_by('id')
        deanon_versions_e: List[Version] = get_reversion_versions(e).order_by('id')

        assert_equal(get_reversion_local_field_dict(deanon_versions_a[0])['name'], 'Lorem')
        assert_equal(get_reversion_local_field_dict(deanon_versions_a[1])['name'], 'LOREM')

        assert_equal(get_reversion_local_field_dict(deanon_versions_b[0])['birth_date'], CUSTOMER__BIRTH_DATE)
        assert_equal(get_reversion_local_field_dict(deanon_versions_b[1])['birth_date'],
                     CUSTOMER__BIRTH_DATE + timedelta(days=2))

        assert_equal(get_reversion_local_field_dict(deanon_versions_c[0])['first_name'], 'Ipsum')
        assert_equal(get_reversion_local_field_dict(deanon_versions_c[1])['first_name'], 'IPSUM')

        assert_equal(get_reversion_local_field_dict(deanon_versions_d[0])['note'], 'sit Amet')
        assert_equal(get_reversion_local_field_dict(deanon_versions_d[1])['note'], 'SIT AMET')

        assert_equal(get_reversion_local_field_dict(deanon_versions_e[0])['last_name'], 'Dolor')
        assert_equal(get_reversion_local_field_dict(deanon_versions_e[1])['last_name'], 'DOLOR')


class TestFileFieldAnonymizer(TestCase):
    def test_file_field(self):
        customer = Customer(**CUSTOMER__KWARGS)
        customer.save()

        avatar = Avatar()
        avatar.customer = customer
        avatar.image.save('test_file_secret_data', ContentFile('Super secret data'), save=False)
        avatar.save()

        avatar_2: Avatar = Avatar.objects.last()
        assert_equal(avatar_2.image.read(), b'Super secret data')
        avatar_2._anonymize_obj(base_encryption_key='LoremIpsumDolorSitAmet')

        avatar_3: Avatar = Avatar.objects.last()
        assert_not_equal(avatar_3.image.read(), b'Super secret data')

        # Cleanup
        avatar_3.image.delete()
        avatar_3.delete()

    def test_file_field_real_file(self):
        anonymizer = anonymizer_register[Avatar]
        anonymizer.image.replacement_file = 'test_file'
        customer = Customer(**CUSTOMER__KWARGS)
        customer.save()

        avatar = Avatar()
        avatar.customer = customer
        avatar.image.save('test_file_real', ContentFile('Super secret data'))

        avatar_2: Avatar = Avatar.objects.last()
        assert_equal(avatar_2.image.read(), b'Super secret data')
        avatar_2._anonymize_obj(base_encryption_key='LoremIpsumDolorSitAmet')

        avatar_3: Avatar = Avatar.objects.last()
        assert_not_equal(avatar_3.image.read(), b'Super secret data')

        anonymizer.image.replacement_file = None
        # Cleanup
        avatar_3.image.delete()
        avatar_3.delete()
