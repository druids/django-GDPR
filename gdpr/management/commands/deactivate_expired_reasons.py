from django.core.management.base import BaseCommand

from gdpr.models import LegalReason

from chamber.utils.tqdm import tqdm

from django.db import transaction


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write('Anonymize expired data of expired legal reasons')
        for legal_reason in tqdm(LegalReason.objects.filter_active_and_expired()):
            legal_reason.expire()
