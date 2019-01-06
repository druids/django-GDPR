"""
Models for test app:

Customer
  - Email
  - Address
  - AccountNumber
    - Payment

"""

from django.db import models

from gdpr.utils import AnonymizationModelMixin


class Customer(models.Model, AnonymizationModelMixin):
    # Keys for pseudoanonymization
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    primary_email_address = models.EmailField(blank=True, null=True)

    full_name = models.CharField(max_length=256, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    personal_id = models.CharField(max_length=10, blank=True, null=True)  # Rodne cislo
    phone_number = models.CharField(max_length=9, blank=True, null=True)
    fb_id = models.CharField(max_length=256, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Just helper method for saving full name.

        You can ignore this method.
        """
        self.full_name = "%s %s" % (self.first_name, self.last_name)
        super().save(*args, **kwargs)


class Email(models.Model, AnonymizationModelMixin):
    """Example on anonymization on related field."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="emails")
    email = models.EmailField(blank=True, null=True)


class Address(models.Model, AnonymizationModelMixin):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    street = models.CharField(max_length=256, blank=True, null=True)
    house_number = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=256, blank=True, null=True)
    post_code = models.CharField(max_length=6, blank=True, null=True)


class Account(models.Model, AnonymizationModelMixin):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="accounts")
    number = models.CharField(max_length=256, blank=True, null=True)
    owner = models.CharField(max_length=256, blank=True, null=True)


class Payment(models.Model, AnonymizationModelMixin):
    """Down the rabbit hole multilevel relations."""
    account_number = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="payments")
    value = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    date = models.DateField(auto_created=True)


class ContactForm(models.Model, AnonymizationModelMixin):
    email = models.EmailField()
    full_name = models.CharField(max_length=256)
