from django.forms import ModelForm, widgets, Textarea
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import ugettext

from users.models import TruffeUser


class EmailFieldLoginWidget(widgets.EmailInput):
    def render(self, name, value, attrs=None):
        content = """<section><label class="input"> <i class="icon-append fa fa-envelope-o"></i>
            <input type="text" name="%s">
            <b class="tooltip tooltip-top-right"><i class="fa fa-envelope-o txt-color-teal"></i> %s</b>
        </label></section>""" % (name, ugettext("Entrez votre adresse mail"))

        return mark_safe(content)

class TruffePasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(TruffePasswordResetForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget = EmailFieldLoginWidget()


class TruffeUserForm(ModelForm):
    class Meta:
        model = TruffeUser
        exclude = ('password', 'last_login', 'is_active', 'date_joined', 'groups', 'user_permissions', 'body', 'homepage')
        widgets = {
            'adresse': Textarea(attrs={'rows': 3}),
        }

    def __init__(self, current_user, *args, **kwargs):
        """Use or not the superuser field"""

        super(TruffeUserForm, self).__init__(*args, **kwargs)

        if not current_user.is_superuser:
            del self.fields['is_superuser']
            del self.fields['username']
            del self.fields['is_betatester']
            del self.fields['first_name']
            del self.fields['last_name']

    def save(self, commit=True):
        instance = super(TruffeUserForm, self).save(commit=False)

        if instance.username_is_sciper():
            instance.password = ''

        if commit:
            instance.save()
        return instance


class TruffeCreateUserForm(ModelForm):
    class Meta:
        model = TruffeUser
        fields = ['email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        """Require first name and last name"""

        super(TruffeCreateUserForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
