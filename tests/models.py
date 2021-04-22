"""
Models for test app:

Customer
  - Email
  - Address
  - AccountNumber
    - Payment

"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from gdpr.mixins import AnonymizationModel
from gdpr.utils import is_reversion_installed
from tests.validators import CZBirthNumberValidator, BankAccountValidator


class CustomerRegistration(AnonymizationModel):
    email_address = models.EmailField(blank=True, null=True)


class Customer(AnonymizationModel):
    # Keys for pseudoanonymization
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    primary_email_address = models.EmailField(blank=True, null=True)

    full_name = models.CharField(max_length=256, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    personal_id = models.CharField(max_length=10, blank=True, null=True, validators=[CZBirthNumberValidator])
    phone_number = models.CharField(max_length=9, blank=True, null=True)
    facebook_id = models.CharField(
        max_length=256, blank=True, null=True,
        verbose_name=_("Facebook ID"), help_text=_("Facebook ID used for login via Facebook."))
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    @property
    def other_registrations(self):
        return CustomerRegistration.objects.filter(email_address=self.primary_email_address).order_by('-pk')[1:]

    @property
    def last_registration(self):
        return CustomerRegistration.objects.filter(email_address=self.primary_email_address).order_by('pk').last()

    def save(self, *args, **kwargs):
        """Just helper method for saving full name.

        You can ignore this method.
        """
        self.full_name = "%s %s" % (self.first_name, self.last_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Email(AnonymizationModel):
    """Example on anonymization on related field."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField(blank=True, null=True)


class Address(AnonymizationModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    street = models.CharField(max_length=256, blank=True, null=True)
    house_number = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=256, blank=True, null=True)
    post_code = models.CharField(max_length=6, blank=True, null=True)


class Account(AnonymizationModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="accounts")
    number = models.CharField(max_length=256, blank=True, null=True, validators=[BankAccountValidator])
    IBAN = models.CharField(max_length=34, blank=True, null=True)
    swift = models.CharField(max_length=11, blank=True, null=True)
    owner = models.CharField(max_length=256, blank=True, null=True)


class Payment(AnonymizationModel):
    """Down the rabbit hole multilevel relations."""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="payments")
    value = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    date = models.DateField(auto_now_add=True)


class ContactForm(AnonymizationModel):
    email = models.EmailField()
    full_name = models.CharField(max_length=256)


class Note(AnonymizationModel):
    note = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


class Avatar(AnonymizationModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="avatars")
    image = models.FileField()


class TopParentA(AnonymizationModel):
    name = models.CharField(max_length=250)


class ParentB(TopParentA):
    birth_date = models.DateField()


class ParentC(ParentB):
    first_name = models.CharField(max_length=250)


class ExtraParentD(AnonymizationModel):
    id_d = models.AutoField(primary_key=True, editable=False)
    note = models.CharField(max_length=250)


class ChildE(ParentC, ExtraParentD):
    last_name = models.CharField(max_length=250)


if is_reversion_installed():
    from reversion import revisions as reversion

    reversion.register(Customer)
    reversion.register(Email)
    reversion.register(Address)
    reversion.register(Account)
    reversion.register(Payment)
    reversion.register(ContactForm)
    reversion.register(Note)
    reversion.register(TopParentA)
    reversion.register(ParentB, follow=('topparenta_ptr',))
    reversion.register(ParentC, follow=('parentb_ptr',))
    reversion.register(ExtraParentD)
    reversion.register(ChildE, follow=('parentc_ptr', 'extraparentd_ptr'))
