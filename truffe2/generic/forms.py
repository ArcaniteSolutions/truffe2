from django.forms import ModelForm


class GenericForm(ModelForm):
    class Meta:
        pass

    def __init__(self, current_user, *args, **kwargs):
        super(GenericForm, self).__init__(*args, **kwargs)
