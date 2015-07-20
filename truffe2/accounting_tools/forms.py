# -*- coding: utf-8 -*-

from django.forms import ModelForm, DateInput
from django.utils.translation import ugettext_lazy as _

from accounting_tools.models import InvoiceLine, SubventionLine, ExpenseClaimLine


class InvoiceLineForm(ModelForm):

    class Meta:
        model = InvoiceLine
        exclude = ('invoice', 'order',)


class SubventionLineForm(ModelForm):

    class Meta:
        model = SubventionLine
        exclude = ('subvention', 'order')

        widgets = {
            'start_date': DateInput(attrs={'class': 'datepicker'}),
            'end_date': DateInput(format='%Y-%m-%d', attrs={'class': 'datepicker'}),
        }


class ExpenseClaimLineForm(ModelForm):

    class Meta:
        model = ExpenseClaimLine
        exclude = ('expense_claim', 'order',)
