from django.utils.translation import gettext_lazy as _

from enumfields import Choice, ChoiceEnum


class LegalReasonState(ChoiceEnum):

    ACTIVE = Choice(1, _('Active'))
    EXPIRED = Choice(2, _('Expired'))
    DEACTIVATED = Choice(3, _('Deactivated'))
