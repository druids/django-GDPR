"""Minimal django settings to run tests."""
from gdpr.utils import is_reversion_installed

DEBUG = True
SECRET_KEY = 'fake-key'
GDPR_KEY = "GDPR_TEST_KEY_PLEASE_CHANGE-#!6_c+78r-q6)@9@z14=3a754929d600$3ll3)(8h0n@cjc*-CHANGE_ME"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "gdpr",
    "tests",
    "django_extensions",
    # Requirements for django-reversion below
    "django.contrib.auth",
    "django.contrib.admin",
]

if is_reversion_installed():
    INSTALLED_APPS += ["reversion"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

USE_TZ = True

# Old legacy settings
# @TODO: Replace
ANONYMIZATION_NAME_KEY = "SOMEFAKEKEY"
ANONYMIZATION_PERSONAL_ID_KEY = 256
ANONYMIZATION_PHONE_KEY = 21212
