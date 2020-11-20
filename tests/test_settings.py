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
    "django.contrib.messages",
    "django.contrib.sessions",
]

if is_reversion_installed():
    INSTALLED_APPS += ["reversion"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE = MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

USE_TZ = True

# Old legacy settings
# @TODO: Replace
ANONYMIZATION_NAME_KEY = "SOMEFAKEKEY"
ANONYMIZATION_PERSONAL_ID_KEY = 256
ANONYMIZATION_PHONE_KEY = 21212
