from django.core.management.base import BaseCommand

from gdpr.models import LegalReason

from tqdm import tqdm

from django.db import transaction


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write('Anonymize expired data of expired legal reasons')
        for legal_reason in tqdm(LegalReason.objects.filter_expired_retaining_data_in_last_days(), ncols=100):
            legal_reason.expire()
