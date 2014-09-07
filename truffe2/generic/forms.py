from django.forms import ModelForm


class GenericForm(ModelForm):
    class Meta:
        pass

    def __init__(self, current_user, *args, **kwargs):
        super(GenericForm, self).__init__(*args, **kwargs)

        if 'user' in self.fields:
            if hasattr(self.Meta.model.MetaData, 'has_unit') and self.Meta.model.MetaData:
                from users.models import TruffeUser
                self.fields['user'].queryset = TruffeUser.objects.filter(accreditation__unit=self.instance.unit, accreditation__end_date=None).distinct().order_by('first_name', 'last_name')

