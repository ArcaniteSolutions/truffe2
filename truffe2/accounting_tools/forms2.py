from django.forms import ModelForm

from accounting_tools.models import ExpenseClaimLine, CashBookLine, ProviderInvoiceLine


class ExpenseClaimLineForm(ModelForm):

    class Meta:
        model = ExpenseClaimLine
        exclude = ('expense_claim', 'order',)

class ProviderInvoiceLineForm(ModelForm):

    class Meta:
        model = ProviderInvoiceLine
        exclude = ('providerInvoice', 'order',)

class CashBookLineForm(ModelForm):

    class Meta:
        model = CashBookLine
        exclude = ('cashbook', 'order',)
