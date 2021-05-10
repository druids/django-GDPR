from django.core.management.base import BaseCommand

from gdpr.models import LegalReason

from chamber.utils.tqdm import tqdm

from django.db import transaction


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Anonymize expired data of expired legal reasons')
        legal_reason_to_expire_qs = LegalReason.objects.filter_active_and_expired()
        for legal_reason in tqdm(legal_reason_to_expire_qs.iterator(),
                                 total=legal_reason_to_expire_qs.count(),
                                 file=self.stdout):
            legal_reason.expire()
