from datetime import timedelta
from typing import List
from unittest import skipIf

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase

from gdpr.anonymizers import ModelAnonymizer
from gdpr.loading import anonymizer_register
from gdpr.utils import is_reversion_installed, get_reversion_local_field_dict
from tests.anonymizers import ContactFormAnonymizer, ChildEAnonymizer
from tests.models import Account, Address, ContactForm, Customer, Email, Note, Payment, Avatar, ChildE
from .data import (
    ACCOUNT__IBAN, ACCOUNT__NUMBER, ACCOUNT__OWNER, ACCOUNT__SWIFT, ADDRESS__CITY, ADDRESS__HOUSE_NUMBER,
    ADDRESS__POST_CODE, ADDRESS__STREET, CUSTOMER__BIRTH_DATE, CUSTOMER__EMAIL, CUSTOMER__EMAIL2, CUSTOMER__EMAIL3,
    CUSTOMER__FACEBOOK_ID, CUSTOMER__FIRST_NAME, CUSTOMER__IP, CUSTOMER__KWARGS, CUSTOMER__LAST_NAME,
    CUSTOMER__PERSONAL_ID, CUSTOMER__PHONE_NUMBER, PAYMENT__VALUE)
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

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')
        self.assertNotEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'last_name')
        self.assertNotEqual(anon_customer.full_name, '%s %s' % (CUSTOMER__FIRST_NAME, CUSTOMER__LAST_NAME))
        self.assertAnonymizedDataExists(anon_customer, 'full_name')
        self.assertNotEqual(anon_customer.primary_email_address, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_customer, 'primary_email_address')
        self.assertNotEqual(anon_customer.personal_id, CUSTOMER__PERSONAL_ID)
        self.assertAnonymizedDataExists(anon_customer, 'personal_id')
        self.assertNotEqual(anon_customer.phone_number, CUSTOMER__PHONE_NUMBER)
        self.assertAnonymizedDataExists(anon_customer, 'phone_number')
        self.assertNotEquals(anon_customer.birth_date, CUSTOMER__BIRTH_DATE)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')
        self.assertNotEquals(anon_customer.facebook_id, CUSTOMER__FACEBOOK_ID)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')
        self.assertNotEqual(str(anon_customer.last_login_ip), CUSTOMER__IP)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

    def test_email(self):
        self.email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        self.email.save()
        self.email._anonymize_obj(base_encryption_key=self.base_encryption_key)
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
        self.address._anonymize_obj(base_encryption_key=self.base_encryption_key)
        anon_address: Address = Address.objects.get(pk=self.address.pk)

        self.assertNotEqual(anon_address.street, ADDRESS__STREET)
        self.assertAnonymizedDataExists(anon_address, 'street')
        self.assertEqual(anon_address.house_number, ADDRESS__HOUSE_NUMBER)
        self.assertEqual(anon_address.city, ADDRESS__CITY)
        self.assertEqual(anon_address.post_code, ADDRESS__POST_CODE)

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

        self.assertNotEqual(anon_account.number, ACCOUNT__NUMBER)
        self.assertAnonymizedDataExists(anon_account, 'number')
        self.assertNotEqual(anon_account.owner, ACCOUNT__OWNER)
        self.assertAnonymizedDataExists(anon_account, 'owner')
        self.assertNotEqual(anon_account.IBAN, ACCOUNT__IBAN)
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

        self.assertNotEquals(anon_payment.value, PAYMENT__VALUE)
        self.assertAnonymizedDataExists(anon_payment, 'value')
        self.assertNotEquals(anon_payment.date, payment_date)
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

        self.assertNotEqual(anon_contact_form.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_contact_form, 'email')
        self.assertNotEqual(anon_contact_form.full_name, FULL_NAME)
        self.assertAnonymizedDataExists(anon_contact_form, 'full_name')

    def test_anonymization_of_anonymized_data(self):
        '''Test that anonymized data are not anonymized again.'''
        self.customer._anonymize_obj()
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        anon_customer._anonymize_obj()
        anon_customer2: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertEqual(anon_customer2.first_name, anon_customer.first_name)
        self.assertNotEqual(anon_customer2.first_name, CUSTOMER__FIRST_NAME)

    def test_anonymization_field_matrix(self):
        self.customer._anonymize_obj(fields=('first_name',))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')

    def test_anonymization_field_matrix_related(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        self.customer._anonymize_obj(fields=('first_name', ('emails', ('email',))))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        self.assertNotEqual(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, 'email')

    def test_anonymization_field_matrix_related_all(self):
        related_email: Email = Email(customer=self.customer, email=CUSTOMER__EMAIL)
        related_email.save()

        self.customer._anonymize_obj(fields=('first_name', ('emails', '__ALL__')))
        anon_customer: Customer = Customer.objects.get(pk=self.customer.pk)

        self.assertNotEqual(anon_customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(anon_customer, 'first_name')

        self.assertEqual(anon_customer.last_name, CUSTOMER__LAST_NAME)
        self.assertAnonymizedDataNotExists(anon_customer, 'last_name')

        anon_related_email: Email = Email.objects.get(pk=related_email.pk)

        self.assertNotEqual(anon_related_email.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_related_email, 'email')

    def test_reverse_generic_relation(self):
        note: Note = Note(note='Test message')
        note.content_object = self.customer
        note.save()

        self.customer._anonymize_obj(fields=(('notes', '__ALL__'),))

        anon_note: Note = Note.objects.get(pk=note.pk)

        self.assertNotEqual(anon_note.note, note.note)
        self.assertAnonymizedDataExists(note, 'note')

        self.customer._deanonymize_obj(fields=(('notes', '__ALL__'),))

        anon_note2: Note = Note.objects.get(pk=note.pk)

        self.assertEqual(anon_note2.note, note.note)
        self.assertAnonymizedDataNotExists(note, 'note')

    def test_irreversible_deanonymization(self):
        contact_form: ContactForm = ContactForm(email=CUSTOMER__EMAIL, full_name=CUSTOMER__LAST_NAME)
        contact_form.save()
        contact_form._anonymize_obj(fields=('__ALL__',))

        self.assertRaises(ModelAnonymizer.IrreversibleAnonymizerException, contact_form._deanonymize_obj,
                          fields=('__ALL__',))

    def test_generic_relation_anonymizer(self):
        contact_form: ContactForm = ContactForm(email=CUSTOMER__EMAIL, full_name=CUSTOMER__LAST_NAME)
        contact_form.save()
        note: Note = Note(note='Test message')
        note.content_object = contact_form
        note.save()

        note._anonymize_obj(fields=(('contact_form', '__ALL__'),), base_encryption_key=self.base_encryption_key)

        anon_contact_form: ContactForm = ContactForm.objects.get(pk=contact_form.pk)

        self.assertNotEqual(anon_contact_form.email, CUSTOMER__EMAIL)
        self.assertAnonymizedDataExists(anon_contact_form, 'email')
        self.assertNotEqual(anon_contact_form.full_name, CUSTOMER__LAST_NAME)
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

        versions: List[Version] = get_reversion_versions(form)

        self.assertEqual(versions[0].field_dict['email'], CUSTOMER__EMAIL)
        self.assertEqual(versions[1].field_dict['email'], CUSTOMER__EMAIL2)
        self.assertEqual(versions[2].field_dict['email'], CUSTOMER__EMAIL3)

        anon.anonymize_obj(form, base_encryption_key=self.base_encryption_key)

        anon_versions: List[Version] = get_reversion_versions(form)
        anon_form = ContactForm.objects.get(pk=form.pk)

        self.assertNotEqual(anon_versions[0].field_dict['email'], CUSTOMER__EMAIL)
        self.assertNotEqual(anon_versions[1].field_dict['email'], CUSTOMER__EMAIL2)
        self.assertNotEqual(anon_versions[2].field_dict['email'], CUSTOMER__EMAIL3)
        self.assertNotEqual(anon_form.email, CUSTOMER__EMAIL3)

        anon.deanonymize_obj(anon_form, base_encryption_key=self.base_encryption_key)

        deanon_versions: List[Version] = get_reversion_versions(form)
        deanon_form = ContactForm.objects.get(pk=form.pk)

        self.assertEqual(deanon_versions[0].field_dict['email'], CUSTOMER__EMAIL)
        self.assertEqual(deanon_versions[1].field_dict['email'], CUSTOMER__EMAIL2)
        self.assertEqual(deanon_versions[2].field_dict['email'], CUSTOMER__EMAIL3)
        self.assertEqual(deanon_form.email, CUSTOMER__EMAIL3)
        self.assertDictEqual(versions[0].field_dict, deanon_versions[0].field_dict)
        self.assertDictEqual(versions[1].field_dict, deanon_versions[1].field_dict)
        self.assertDictEqual(versions[2].field_dict, deanon_versions[2].field_dict)

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

        versions_a: List[Version] = get_reversion_versions(e.topparenta_ptr)
        versions_b: List[Version] = get_reversion_versions(e.parentb_ptr)
        versions_c: List[Version] = get_reversion_versions(e.parentc_ptr)
        versions_d: List[Version] = get_reversion_versions(e.extraparentd_ptr)
        versions_e: List[Version] = get_reversion_versions(e)

        self.assertEqual(get_reversion_local_field_dict(versions_a[0])['name'], 'Lorem')
        self.assertEqual(get_reversion_local_field_dict(versions_a[1])['name'], 'LOREM')

        self.assertEqual(get_reversion_local_field_dict(versions_b[0])['birth_date'], CUSTOMER__BIRTH_DATE)
        self.assertEqual(get_reversion_local_field_dict(versions_b[1])['birth_date'],
                         CUSTOMER__BIRTH_DATE + timedelta(days=2))

        self.assertEqual(get_reversion_local_field_dict(versions_c[0])['first_name'], 'Ipsum')
        self.assertEqual(get_reversion_local_field_dict(versions_c[1])['first_name'], 'IPSUM')

        self.assertEqual(get_reversion_local_field_dict(versions_d[0])['note'], 'sit Amet')
        self.assertEqual(get_reversion_local_field_dict(versions_d[1])['note'], 'SIT AMET')

        self.assertEqual(get_reversion_local_field_dict(versions_e[0])['last_name'], 'Dolor')
        self.assertEqual(get_reversion_local_field_dict(versions_e[1])['last_name'], 'DOLOR')

        anon.anonymize_obj(e, base_encryption_key=self.base_encryption_key)

        anon_versions_a: List[Version] = get_reversion_versions(e.topparenta_ptr)
        anon_versions_b: List[Version] = get_reversion_versions(e.parentb_ptr)
        anon_versions_c: List[Version] = get_reversion_versions(e.parentc_ptr)
        anon_versions_d: List[Version] = get_reversion_versions(e.extraparentd_ptr)
        anon_versions_e: List[Version] = get_reversion_versions(e)
        anon_e = ChildE.objects.get(pk=e.pk)

        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_a[0])['name'], 'Lorem')
        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_a[1])['name'], 'LOREM')

        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_b[0])['birth_date'], CUSTOMER__BIRTH_DATE)
        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_b[1])['birth_date'],
                            CUSTOMER__BIRTH_DATE + timedelta(days=2))

        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_c[0])['first_name'], 'Ipsum')
        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_c[1])['first_name'], 'IPSUM')

        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_d[0])['note'], 'sit Amet')
        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_d[1])['note'], 'SIT AMET')

        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_e[0])['last_name'], 'Dolor')
        self.assertNotEqual(get_reversion_local_field_dict(anon_versions_e[1])['last_name'], 'DOLOR')

        anon.deanonymize_obj(anon_e, base_encryption_key=self.base_encryption_key)

        deanon_versions_a: List[Version] = get_reversion_versions(e.topparenta_ptr)
        deanon_versions_b: List[Version] = get_reversion_versions(e.parentb_ptr)
        deanon_versions_c: List[Version] = get_reversion_versions(e.parentc_ptr)
        deanon_versions_d: List[Version] = get_reversion_versions(e.extraparentd_ptr)
        deanon_versions_e: List[Version] = get_reversion_versions(e)

        self.assertEqual(get_reversion_local_field_dict(deanon_versions_a[0])['name'], 'Lorem')
        self.assertEqual(get_reversion_local_field_dict(deanon_versions_a[1])['name'], 'LOREM')

        self.assertEqual(get_reversion_local_field_dict(deanon_versions_b[0])['birth_date'], CUSTOMER__BIRTH_DATE)
        self.assertEqual(get_reversion_local_field_dict(deanon_versions_b[1])['birth_date'],
                         CUSTOMER__BIRTH_DATE + timedelta(days=2))

        self.assertEqual(get_reversion_local_field_dict(deanon_versions_c[0])['first_name'], 'Ipsum')
        self.assertEqual(get_reversion_local_field_dict(deanon_versions_c[1])['first_name'], 'IPSUM')

        self.assertEqual(get_reversion_local_field_dict(deanon_versions_d[0])['note'], 'sit Amet')
        self.assertEqual(get_reversion_local_field_dict(deanon_versions_d[1])['note'], 'SIT AMET')

        self.assertEqual(get_reversion_local_field_dict(deanon_versions_e[0])['last_name'], 'Dolor')
        self.assertEqual(get_reversion_local_field_dict(deanon_versions_e[1])['last_name'], 'DOLOR')


class TestFileFieldAnonymizer(TestCase):
    def test_file_field(self):
        customer = Customer(**CUSTOMER__KWARGS)
        customer.save()

        avatar = Avatar()
        avatar.customer = customer
        avatar.image.save('test_file_secret_data', ContentFile('Super secret data'), save=False)
        avatar.save()

        avatar_2: Avatar = Avatar.objects.last()
        self.assertEqual(avatar_2.image.read(), b'Super secret data')
        avatar_2._anonymize_obj(base_encryption_key='LoremIpsumDolorSitAmet')

        avatar_3: Avatar = Avatar.objects.last()
        self.assertNotEqual(avatar_3.image.read(), b'Super secret data')

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
        self.assertEqual(avatar_2.image.read(), b'Super secret data')
        avatar_2._anonymize_obj(base_encryption_key='LoremIpsumDolorSitAmet')

        avatar_3: Avatar = Avatar.objects.last()
        self.assertNotEqual(avatar_3.image.read(), b'Super secret data')

        anonymizer.image.replacement_file = None
        # Cleanup
        avatar_3.image.delete()
        avatar_3.delete()
