from django.core.management.base import BaseCommand, CommandError
from users.models import TruffeUser, UserPrivacy

import json


class Command(BaseCommand):
    help = 'Dump users'

    def handle(self, *args, **options):

        LEVEL_MAPPING = {
            'prive': 'private',
            'groupe': 'com',
            'member': 'agep',
            'public': 'all'
        }

        retour = []

        for user in TruffeUser.objects.all():

            data = {
                'username': user.username,
                'emailEpfl': user.email,
                'prenom': user.first_name,
                'nom': user.last_name,
                'mobile': user.mobile,
                'adresse': user.adresse,
                'banque': user.nom_banque,
                'ibanOrCcp': user.iban_ou_ccp,
                'emailPerso': user.email_perso,
                'password': user.password,
                'mobileVisibility': LEVEL_MAPPING.get(UserPrivacy.get_privacy_for_field(user, 'mobile')),
                'adresseVisibility': LEVEL_MAPPING.get(UserPrivacy.get_privacy_for_field(user, 'adresse')),
                'banqueVisibility': LEVEL_MAPPING.get(UserPrivacy.get_privacy_for_field(user, 'nom_banque')),
                'ibanOrCcpVisibility': LEVEL_MAPPING.get(UserPrivacy.get_privacy_for_field(user, 'iban_ou_ccp')),
            }


            retour.append(data)

        print json.dumps({'data': retour})
