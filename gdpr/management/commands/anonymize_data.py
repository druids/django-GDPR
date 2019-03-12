import math

import pyprind
from django.core.management.base import BaseCommand
from utils import chunked_iterator, chunked_queryset_iterator
from utils.commands import ProgressBarStream

from gdpr.anonymizers import DeleteModelAnonymizer
from gdpr.loading import anonymizer_register


class Command(BaseCommand):
    help = 'Anonymize database data according to defined anonymizers in applications.'

    def add_arguments(self, parser):
        parser.add_argument('--models', type=str, action='store', dest='models',
                            help='name of the anonymized models ("app_name.model_name") separated by a comma.')

    def _anonymize_by_qs(self, obj_anonymizer, qs):
        bar = pyprind.ProgBar(
            max(math.ceil(qs.count() // obj_anonymizer.chunk_size), 1),
            title='Anonymize model {}'.format(self._get_full_model_name(qs.model)),
            stream=ProgressBarStream(self.stdout)
        )
        for batch_qs in chunked_queryset_iterator(qs, obj_anonymizer.chunk_size, delete_qs=isinstance(
                obj_anonymizer, DeleteModelAnonymizer)):
            obj_anonymizer().anonymize_qs(batch_qs)
            bar.update()

    def _anonymize_by_obj(self, obj_anonymizer, qs):
        bar = pyprind.ProgBar(
            qs.count(),
            title='Anonymize model {}'.format(self._get_full_model_name(qs.model)),
            stream=ProgressBarStream(self.stdout)
        )
        for obj in chunked_iterator(qs, obj_anonymizer.chunk_size):
            obj_anonymizer().anonymize_obj(obj)
            bar.update()

    def _anonymize(self, obj_anonymizer, model):
        qs = model.objects.all()
        if obj_anonymizer.can_anonymize_qs:
            self._anonymize_by_qs(obj_anonymizer, qs)
        else:
            self._anonymize_by_obj(obj_anonymizer, qs)

    def _get_full_model_name(self, model):
        return '{}.{}'.format(model._meta.app_label, model._meta.model_name)

    def handle(self, models, *args, **options):
        models = {v.strip().lower() for v in models.split(',')} if models else None
        for obj_anonymizer in list(anonymizer_register()):
            model = obj_anonymizer.Meta.model
            if not models or self._get_full_model_name(model) in models:
                self._anonymize(obj_anonymizer, model)
        self.stdout.write('Data was anonymized')
