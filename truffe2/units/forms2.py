from django.forms import ModelForm, CharField, ValidationError
from django.utils.translation import ugettext_lazy as _

from units.models import Accreditation
from users.models import TruffeUser

import re


class AccreditationAddForm(ModelForm):

    user = CharField()

    class Meta:
        model = Accreditation
        exclude = ('start_date', 'end_date', 'validation_date', 'unit', 'user')

    def __init__(self, current_user, *args, **kwargs):
        """"""

        super(AccreditationAddForm, self).__init__(*args, **kwargs)

        # if not current_user.is_superuser:
        #     del self.fields['is_superuser']

    def clean_user(self):
        data = self.cleaned_data['user']
        if not re.match('^\d{6}$', data):
            try:
                TruffeUser.objects.get(username=data)
            except TruffeUser.DoesNotExist:
                raise ValidationError(_('Pas un username valide'))

        return data
