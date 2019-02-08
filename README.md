# Django-GDPR [![Build Status](https://travis-ci.org/BrnoPCmaniak/django-GDPR.svg?branch=develop)](https://travis-ci.org/BrnoPCmaniak/django-GDPR)

This libarary enables you to store user's consent for data retention easily
and to anonymize/deanonymize user's data accordingly.

For brief overview you can check example app in `tests` directory.

# Quickstart

Install django-gdpr with pip:

```bash
pip install django-gdpr
```

Add gdpr to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Django apps...
    'gdpr',
]
```

Imagine having a customer model:

```python
# app/models.py

from django.db import models

from gdpr.mixins import AnonymizationModel

class Customer(AnonymizationModel):
    # Keys for pseudoanonymization
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)

    birth_date = models.DateField(blank=True, null=True)
    personal_id = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=9, blank=True, null=True)
    fb_id = models.CharField(max_length=256, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
```

You may want a consent to store all user's data for two years and consent to store first and last name for 10 years.
For that you can simply add new consent purposes like this.

```python
# app/purposes.py

from dateutil.relativedelta import relativedelta

from gdpr.purposes.default import AbstractPurpose

GENERAL_PURPOSE_SLUG = "general"
FIRST_N_LAST_NAME_SLUG = "first_n_last"

class GeneralPurpose(AbstractPurpose):
    name = "Retain user data for 2 years"
    slug = GENERAL_PURPOSE_SLUG
    expiration_timedelta = relativedelta(years=2)
    fields = "__ALL__"  # Anonymize all fields defined in anonymizer

class FirstNLastNamePurpose(AbstractPurpose):
    """Store First & Last name for 10 years."""
    name = "retain due to internet archive"
    slug = FIRST_N_LAST_NAME_SLUG
    expiration_timedelta = relativedelta(years=10)
    fields = ("first_name", "last_name")
```

The fields `fields` specify to which fields this consent applies to.

Some more examples:
```python
fields = ("first_name", "last_name") # Anonymize only two fields

# You can also add nested fields to anonymize fields on related objects.
fields = (
    "primary_email_address",
    ("emails", (
        "email",
    )),
)

# Some more advanced configs may look like this:
fields = (
    "__ALL__",
    ("addresses", "__ALL__"),
    ("accounts", (
        "__ALL__",
        ("payments", (
            "__ALL__",
        ))
    )),
    ("emails", (
        "email",
    )),
)

```

Now when we have purpose created we also have to make a *anonymizer* so the library knows which fields and how to
anonymize this is fairly simple and is really similar to Django forms.

```python
# app/anonymizers.py

from gdpr import anonymizers
from tests.models import Customer


class CustomerAnonymizer(anonymizers.ModelAnonymizer):
    first_name = anonymizers.MD5TextFieldAnonymizer()
    last_name = anonymizers.MD5TextFieldAnonymizer()
    primary_email_address = anonymizers.EmailFieldAnonymizer()

    birth_date = anonymizers.DateFieldAnonymizer()
    personal_id = anonymizers.PersonalIIDFieldAnonymizer()
    phone_number = anonymizers.PhoneFieldAnonymizer()
    fb_id = anonymizers.CharFieldAnonymizer()
    last_login_ip = anonymizers.IPAddressFieldAnonymizer()

    class Meta:
        model = Customer
```

Now you can fully leverage the system:

You can create new consent:
```python
from gdpr.models import LegalReason

from tests.models import Customer
from tests.purposes import FIRST_N_LAST_NAME_SLUG

customer = Customer(first_name="John", last_name="Smith")
customer.save()

LegalReason.objects.create_consent(FIRST_N_LAST_NAME_SLUG, customer)
```

And you can revoke it if needed:
```python
from gdpr.models import LegalReason

from tests.models import Customer
from tests.purposes import FIRST_N_LAST_NAME_SLUG

customer = Customer.objects.get(first_name="John", last_name="Smith")


LegalReason.objects.expire_consent(FIRST_N_LAST_NAME_SLUG, customer)
```

Once in some optimal amount of time (a day) you should invoke
following command to revoke all expired consents.

```python
from gdpr.models import LegalReason

LegalReason.objects.expire_old_consents()
```

## FieldAnonymizers

* `FunctionAnonymizer` - in situ anonymization method (`secret_code = anonymizers.FunctionFieldAnonymizer(lambda x: x**2)`)
* `PlaceHolderAnonymizer` - placeholder
* `DateFieldAnonymizer`
* `CharFieldAnonymizer`
* `DecimalFieldAnonymizer`
* `IPAddressFieldAnonymizer`
* `CzechAccountNumberFieldAnonymizer` - for czech bank account numbers
* `JSONFieldAnonymizer`
* `EmailFieldAnonymizer`
* `MD5TextFieldAnonymizer`
* `SHA256TextFieldAnonymizer`
* `HashTextFieldAnonymizer` - anonymization with given hash algorithm (`secret_code = anonymizers.HashTextFieldAnonymizer('sha512')`)
* `StaticValueAnonymizer` - for anonymization replace with static value (`secret_code = anonymizers.StaticValueAnonymizer(42)`)
