from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.html import escape

from .models import DisplayReservationLine, Display

class DisplayReservationLineForm(ModelForm):
    
    class Meta:
        model = DisplayReservationLine
        exclude = ('display_reservation', 'order')
    
    def __init__(self, *args, **kwargs):
        
        super(DisplayReservationLineForm, self).__init__(*args, **kwargs)
        self.fields['display'].queryset = Display.objects.filter(active=True, deleted=False).order_by('unit__name', 'title')
        
        self.fields['display'].label_from_instance = lambda obj: mark_safe(u"[{}] {}".format(escape(obj.unit), escape(obj.title)))