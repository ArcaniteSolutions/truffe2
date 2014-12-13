from django.forms import ModelForm, Form, CharField, ChoiceField, Textarea
from django.utils.translation import ugettext_lazy as _


class GenericForm(ModelForm):
    class Meta:
        pass

    def __init__(self, current_user, *args, **kwargs):
        super(GenericForm, self).__init__(*args, **kwargs)

        if 'user' in self.fields:
            if hasattr(self.Meta.model.MetaData, 'has_unit') and self.Meta.model.MetaData:
                from users.models import TruffeUser
                self.fields['user'].queryset = TruffeUser.objects.filter(accreditation__unit=self.instance.unit, accreditation__end_date=None).distinct().order_by('first_name', 'last_name')


class ContactForm(Form):

    subject = CharField(label=_('Sujet'), max_length=100)
    message = CharField(label=_('Message'), widget=Textarea)

    def __init__(self, keys, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

        choices_key = [x for x in keys.iteritems()]

        self.fields['key'] = ChoiceField(label=_('Destinataire(s)'), choices=choices_key)
