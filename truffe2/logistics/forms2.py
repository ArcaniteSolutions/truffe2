from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.html import escape


from .models import SupplyReservationLine, Supply


class SupplyReservationLineForm(ModelForm):

    class Meta:
        model = SupplyReservationLine
        exclude = ('supply_reservation', 'order')

    def __init__(self, *args, **kwargs):

        super(SupplyReservationLineForm, self).__init__(*args, **kwargs)
        self.fields['supply'].queryset = Supply.objects.filter(active=True, deleted=False).order_by('unit__name', 'title')

        self.fields['supply'].label_from_instance = lambda obj: mark_safe(u"[{}] {} ({})".format(escape(obj.unit), escape(obj.title), obj.quantity))
