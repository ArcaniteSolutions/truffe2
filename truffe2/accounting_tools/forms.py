# -*- coding: utf-8 -*-

from django.forms import ModelForm, DateInput

from accounting_tools.models import SubventionLine


class SubventionLineForm(ModelForm):

    class Meta:
        model = SubventionLine
        exclude = ('subvention', 'order')

        widgets = {
            'start_date': DateInput(attrs={'class': 'datepicker'}),
            'end_date': DateInput(format='%Y-%m-%d', attrs={'class': 'datepicker'}),
        }
