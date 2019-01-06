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
        'NAME': 'db',
    }
}

USE_TZ = True
