#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    failures = TestRunner = get_runner(settings)().run_tests(["tests", "gdpr"])
    sys.exit(bool(failures))
