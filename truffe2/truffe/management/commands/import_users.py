from django.core.management.base import BaseCommand, CommandError
from users.models import TruffeUser, UserPrivacy

import json
import sys
import string


class Command(BaseCommand):
    help = 'Import users'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        for user in data['data']:

            truffe_user, __ = TruffeUser.objects.get_or_create(username=user['username'])

            truffe_user.email = user['emailEpfl']
            truffe_user.first_name = string.capwords(user['prenom'])
            truffe_user.last_name = string.capwords(user['nom'])
            truffe_user.is_active = True
            truffe_user.mobile = user['mobile']
            truffe_user.adresse = user['adresse']
            truffe_user.nom_banque = user['banque']
            truffe_user.iban_ou_ccp = user['ibanOrCcp']

            if user['password']:
                truffe_user.password = user['password']

            truffe_user.save()

            LEVEL_MAPPING = {
                'private': 'prive',
                'com': 'groupe',
                'agep': 'member',
                'all': 'public'
            }

            up, __ = UserPrivacy.objects.get_or_create(user=truffe_user, field='mobile')
            up.level = LEVEL_MAPPING.get(user['mobileVisibility'])
            up.save()

            up, __ = UserPrivacy.objects.get_or_create(user=truffe_user, field='adresse')
            up.level = LEVEL_MAPPING.get(user['adresseVisibility'])
            up.save()

            up, __ = UserPrivacy.objects.get_or_create(user=truffe_user, field='nom_banque')
            up.level = LEVEL_MAPPING.get(user['banqueVisibility'])
            up.save()

            up, __ = UserPrivacy.objects.get_or_create(user=truffe_user, field='iban_ou_ccp')
            up.level = LEVEL_MAPPING.get(user['ibanOrCcpVisibility'])
            up.save()

            # {u'twitterVisibility': u'com',
            # u'usePersoAsEmail': False,
            # u'skype': u'-lionel'
            # , u'usernameIsSciper': True,
            # u'gmail': u'xxx@gmail.com'
            # u'mobileVisibility': u'com'
            # , u'emailPersoVisibility': u'com',
            # u'jabber': u'',
            # u'jabberVisibility': u'com',
            # u'avatarVisibility': u'private',
            # u'personnalDetailsSaved': True,
            # u'gmailVisibility': u'com',
            # u'facebookVisibility': u'com',
            # u'twitter': u'',
            # u'emailPerso': u'',
            # u'facebook': u'',
            # , u'skypeVisibility': u'com',
            # u'avatar': u''}
