from django.forms import ModelForm

from users.models import TruffeUser


class TruffeUserForm(ModelForm):
    class Meta:
        model = TruffeUser
        exclude = ('username', 'password', 'last_login', 'email', 'is_active', 'is_superuser', 'date_joined', 'first_name', 'last_name', 'groups', 'user_permissions')

