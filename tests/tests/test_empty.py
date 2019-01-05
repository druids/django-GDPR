from django.test import TestCase


class EmptyTests(TestCase):
    def test_this_test_is_run(self):
        """Test that the test suite is running this tests."""
        self.assertTrue(True)

    def test_GDPR_app_is_reachable(self):
        """Test that GDPR app is reachable."""
        from gdpr.version import get_version
        get_version()
        self.assertTrue(True)
