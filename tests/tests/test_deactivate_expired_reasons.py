from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from django.test import TestCase, override_settings

from freezegun import freeze_time
from gdpr.models import LegalReason
from germanium.tools import assert_equal, assert_false, assert_not_equal, assert_true, test_call_command
from tests.models import Customer
from tests.purposes import FIRST_AND_LAST_NAME_SLUG, MARKETING_SLUG
from tests.tests.data import CUSTOMER__FIRST_NAME, CUSTOMER__KWARGS
from tests.tests.utils import AnonymizedDataMixin


class TestDeactivateExpiredReasons(AnonymizedDataMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.customer: Customer = Customer(**CUSTOMER__KWARGS)
        cls.customer.save()

    def test_command_should_expire_active_legal_reson(self):
        legal_reason = LegalReason.objects.create_consent(MARKETING_SLUG, self.customer)
        legal_reason.save()

        # consent has not expired
        test_call_command('deactivate_expired_reasons')
        assert_true(LegalReason.objects.exists_valid_consent(MARKETING_SLUG, self.customer))

        # consent has expired
        with freeze_time(legal_reason.expires_at + relativedelta(seconds=1)):
            test_call_command('deactivate_expired_reasons')
        assert_false(LegalReason.objects.exists_valid_consent(MARKETING_SLUG, self.customer))

    def test_command_should_not_expire_deactivated_legal_reasons(self):
        legal_reason = LegalReason.objects.create_consent(MARKETING_SLUG, self.customer)
        legal_reason.save()
        legal_reason.deactivate()

        # consent has not expired
        test_call_command('deactivate_expired_reasons')
        assert_true(LegalReason.objects.exists_deactivated_consent(MARKETING_SLUG, self.customer))

        # consent has expired
        with freeze_time(legal_reason.expires_at + relativedelta(seconds=1)):
            test_call_command('deactivate_expired_reasons')
        assert_true(LegalReason.objects.exists_deactivated_consent(MARKETING_SLUG, self.customer))

    def test_command_should_not_touch_already_expired_legal_reasons(self):
        legal_reason = LegalReason.objects.create_consent(MARKETING_SLUG, self.customer)
        legal_reason.save()
        legal_reason.expire()
        original_expiration_time = legal_reason.changed_at

        with freeze_time(original_expiration_time + relativedelta(seconds=1)):
            test_call_command('deactivate_expired_reasons')
        assert_equal(original_expiration_time, legal_reason.refresh_from_db().changed_at)

    def test_command_should_not_anonymize_customer_if_expiring_reason_is_not_related_to_customer_data(self):
        marketing_legal_reason = LegalReason.objects.create_consent(MARKETING_SLUG, self.customer)
        marketing_legal_reason.save()
        LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer).save()

        # none of the consents have expired
        test_call_command('deactivate_expired_reasons')
        assert_true(LegalReason.objects.exists_valid_consent(MARKETING_SLUG, self.customer))
        assert_true(LegalReason.objects.exists_valid_consent(FIRST_AND_LAST_NAME_SLUG, self.customer))

        # marketing consent has expired
        with freeze_time(marketing_legal_reason.expires_at + relativedelta(seconds=1)):
            test_call_command('deactivate_expired_reasons')
        assert_false(LegalReason.objects.exists_valid_consent(MARKETING_SLUG, self.customer))
        assert_true(LegalReason.objects.exists_valid_consent(FIRST_AND_LAST_NAME_SLUG, self.customer))
        assert_equal(self.customer.first_name, CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataNotExists(self.customer, 'first_name')
        assert_not_equal(self.customer._anonymize_obj(), CUSTOMER__FIRST_NAME)
        self.assertAnonymizedDataExists(self.customer, 'first_name')

    @override_settings(GDPR_DEACTIVATE_EXPIRED_REASONS_CHUNK_SIZE=1)
    def test_command_should_support_chunking(self):
        legal_reason1 = LegalReason.objects.create_consent(MARKETING_SLUG, self.customer)
        legal_reason1.save()
        legal_reason2 = LegalReason.objects.create_consent(FIRST_AND_LAST_NAME_SLUG, self.customer)
        legal_reason2.save()

        with freeze_time(max(legal_reason1.expires_at, legal_reason2.expires_at) + relativedelta(seconds=1)):
            with patch('gdpr.management.commands.deactivate_expired_reasons.logger.info') as logger_mock:
                assert_equal(LegalReason.objects.filter_active().count(), 2)
                test_call_command('deactivate_expired_reasons')
                assert_equal(LegalReason.objects.filter_active().count(), 1)
                test_call_command('deactivate_expired_reasons')
                assert_equal(LegalReason.objects.filter_active().count(), 0)
                logger_mock.assert_called_once_with('Command "deactivate_expired_reasons" finished')
