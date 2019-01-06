"""Minimal django settings to run tests."""

SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "gdpr",
    "tests",
    "django_extensions",
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

USE_TZ = True

# Old HC settings
# @TODO: Replace
ANONYMIZATION_NAME_KEY = "SOMEFAKEKEY"
ANONYMIZATION_PERSONAL_ID_KEY = 256
ANONYMIZATION_PHONE_KEY = 21212
