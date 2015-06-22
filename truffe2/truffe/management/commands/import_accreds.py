from django.core.management.base import BaseCommand, CommandError
from users.models import TruffeUser
from units.models import Unit, Role, Accreditation

from django.utils.timezone import now
import datetime
import pytz

import json
import sys


class Command(BaseCommand):
    help = 'Import accreds'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        accred_date = now()
        paris_tz = pytz.timezone("Europe/Paris")

        for unit_data in data['data']:
            try:
                unit = Unit.objects.get(name=unit_data['name'])
            except:
                print u"Unit not found !!", unit_data['name']
                unit = None

            if unit:

                for accred_data in unit_data['accreds']:

                    try:
                        role = Role.objects.get(name=accred_data['role'])
                    except:
                        print u"Role not found", accred_data['role']
                        role = None

                    try:
                        user = TruffeUser.objects.get(username=accred_data['user'])
                    except:
                        print u"User not found", accred_data['user']
                        user = None

                    if role and user:

                        if accred_data['start'] == 'None':
                            print 'Accred with start=None oO ?'

                        else:

                            start_date = paris_tz.localize(datetime.datetime.strptime(accred_data['start'], '%Y-%m-%d %H:%M:%S'))
                            if accred_data['end'] and accred_data['end'] != 'None':
                                end_date = paris_tz.localize(datetime.datetime.strptime(accred_data['end'], '%Y-%m-%d %H:%M:%S'))
                            else:
                                end_date = None

                            accred, __ = Accreditation.objects.get_or_create(unit=unit, user=user, role=role, start_date=start_date, end_date=end_date)
                            accred.display_name = accred_data['customName']
                            accred.renewal_date = accred_date
                            accred.start_date = start_date
                            accred.end_date = end_date
                            accred.save()

        Accreditation.objects.exclude(renewal_date=accred_date).delete()
