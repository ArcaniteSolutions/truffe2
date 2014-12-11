# Tequila auth for django

# Version 1.0, 15.08.2010
# (C) Maximilien Cuony 2010
# BSD License

import urllib
import re
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login, authenticate
from django.conf import settings


User = get_user_model()


def get_request_key(request):
    """Ask tequla server for the key"""

    params = "urlaccess=" + request.build_absolute_uri() + "\nservice=" + settings.TEQUILA_SERVICE + "\nrequest=name,firstname,email,uniqueid"
    f = urllib.urlopen(settings.TEQUILA_SERVER + '/cgi-bin/tequila/createrequest', params)
    return re.search('key=(.*)', f.read()).group(1)


class Backend:
    """Backend to authenticate users"""

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, token=None):

        # Check if token is valid
        params = 'key=' + token
        f = urllib.urlopen(settings.TEQUILA_SERVER + '/cgi-bin/tequila/fetchattributes', params)
        data = f.read()

        if data.find('status=ok') == -1:
            return None

        # Get informations about user
        firstName = re.search('\nfirstname=(.*)', data).group(1)
        name = re.search('\nname=(.*)', data).group(1)
        email = re.search('\nemail=(.*)', data).group(1)
        sciper = re.search('\nuniqueid=(.*)', data).group(1)

        # Find user in database
        try:
            user = User.objects.get(username=sciper)
        except User.DoesNotExist:

            # Should we create it ?
            if settings.TEQUILA_AUTOCREATE:
                user = User()
                user.username = sciper
                user.first_name = firstName.split(',')[0]
                user.last_name = name.split(',')[0]
                user.email = email
                user.save()
            else:
                user = None

        return user


def login(request):

    key = request.GET.get('key', '')

    # Return from tequila ?
    if key != '':

        user = authenticate(token=key)

        if user is not None:  # Try to auth
            if user.is_active:
                auth_login(request, user)  # Youpie !

                # Get url to go now. If there is a non-empty string in the cookie
                # we use it, otherwise we default, LOGIN_REDIRECT_URL in settings
                if 'login_redirect' in request.COOKIES:
                    if request.COOKIES['login_redirect'] != '':
                        goTo = request.COOKIES['login_redirect']
                    else:
                        goTo = settings.LOGIN_REDIRECT_URL
                else:
                    goTo = settings.LOGIN_REDIRECT_URL

                return HttpResponseRedirect(goTo)
            else:
                return render_failure(request, 'disabled')
        else:
            return render_failure(request, 'genericerror')
    else:
        r = HttpResponseRedirect(settings.TEQUILA_SERVER + '/cgi-bin/tequila/requestauth?requestkey=' + get_request_key(request))

        # Set the cookie to be redirected when auth is done
        next = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
        r.set_cookie('login_redirect', next)

        return r


# Redirect to error
def render_failure(request, string):
    return HttpResponseRedirect(settings.TEQUILA_FAILURE + '?why=' + string)
