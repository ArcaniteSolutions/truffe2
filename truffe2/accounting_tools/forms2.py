from django.forms import ModelForm


from accounting_tools.models import ExpenseClaimLine


class ExpenseClaimLineForm(ModelForm):

    class Meta:
        model = ExpenseClaimLine
        exclude = ('expense_claim', 'order',)
