from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from accounting_tools.models import InvoiceLine


class InvoiceLineForm(ModelForm):

    class Meta:
        model = InvoiceLine
        exclude = ('invoice', 'order',)
