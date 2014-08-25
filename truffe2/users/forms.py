from django.forms import ModelForm

from users.models import TruffeUser


class TruffeUserForm(ModelForm):
    class Meta:
        model = TruffeUser
        exclude = ('username', 'password', 'last_login', 'email', 'is_active', 'date_joined', 'first_name', 'last_name', 'groups', 'user_permissions', 'body')

    def __init__(self, current_user, *args, **kwargs):
        """Use or not the superuser field"""

        super(TruffeUserForm, self).__init__(*args, **kwargs)

        if not current_user.is_superuser:
            del self.fields['is_superuser']
