# -*- coding: utf-8 -*-

from django.forms import ModelForm

from accounting_tools.models import SubventionLine


class SubventionLineForm(ModelForm):

    class Meta:
        model = SubventionLine
        exclude = ('subvention',)
