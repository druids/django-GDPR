from django.core.management.base import BaseCommand

from gdpr.models import LegalReason


class Command(BaseCommand):

    def handle(self, *args, **options):

        for legal_reason in LegalReason.objects.filter_expired_retaining_data_in_last_days():
            legal_reason._expirement()
