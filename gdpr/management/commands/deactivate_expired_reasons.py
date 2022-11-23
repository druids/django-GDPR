import logging

from django.core.management.base import BaseCommand

from gdpr.models import LegalReason

from chamber.utils.tqdm import tqdm

from django.conf import settings
from django.db import transaction


logger = logging.getLogger(getattr(settings, 'GDPR_DEACTIVATE_EXPIRED_REASONS_LOGGER', __name__))


class Command(BaseCommand):

    def _slice_queryset(self, queryset):
        chunk_size = getattr(settings, 'GDPR_DEACTIVATE_EXPIRED_REASONS_CHUNK_SIZE', None)
        return queryset[:chunk_size] if chunk_size else queryset

    def handle(self, *args, **options):
        self.stdout.write('Anonymize expired data of expired legal reasons')

        legal_reason_to_expire_qs = LegalReason.objects.filter_active_and_expired()
        total_number_of_objects = legal_reason_to_expire_qs.count()
        sliced_qs = self._slice_queryset(legal_reason_to_expire_qs)

        for legal_reason in tqdm(sliced_qs.iterator(), total=sliced_qs.count(), file=self.stdout):
            legal_reason.expire()

        remaining_number_of_objects = legal_reason_to_expire_qs.count()

        self.stdout.write(
            f'  Total number of expired reasons: {total_number_of_objects}'
        )
        self.stdout.write(
            f'  Remaining number of expired reasons: {remaining_number_of_objects}'
        )

        if remaining_number_of_objects == 0:
            logger.info('Command "deactivate_expired_reasons" finished')
