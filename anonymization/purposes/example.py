from datetime import timedelta
from anonymization.purposes.default import AbstractPurpose


class ExamplePurpose(AbstractPurpose):
    name = 'Example purpose'
    slug = 'example'
    fields = {
        'customer': ('first_name', 'last_name'),
        'order': ('items',),
    }
    expires_in = timedelta(year=1)
