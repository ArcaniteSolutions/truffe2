# -*- coding: utf-8 -*-

from django.forms import ModelForm, CharField, ValidationError
from django.utils.translation import ugettext_lazy as _

from members.models import Membership
from users.models import TruffeUser

import re


class MembershipAddForm(ModelForm):

    user = CharField()

    class Meta:
        model = Membership
        exclude = ('start_date', 'end_date', 'user', 'group')

    def __init__(self, current_user, *args, **kwargs):
        """"""
        group = kwargs.pop('group')
        super(MembershipAddForm, self).__init__(*args, **kwargs)

        if not group or not group.handle_fees:
            del self.fields['payed_fees']

    def clean_user(self):
        data = self.cleaned_data['user']
        if not re.match('^\d{6}$', data):
            try:
                TruffeUser.objects.get(username=data)
            except TruffeUser.DoesNotExist:
                raise ValidationError(_('Pas un username valide'))

        return data

    def clean(self):
        cleaned_data = super(MembershipAddForm, self).clean()

        if cleaned_data.get('generates_accred') and cleaned_data.get('generated_accred_type') is None:
            raise ValidationError(u"Ne peut pas avoir un type nul si une accréditation est générée.")

        return cleaned_data
