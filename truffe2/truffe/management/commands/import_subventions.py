# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from accounting_core.models import AccountingYear
from accounting_tools.models import Subvention, SubventionLine, SubventionLogging, SubventionFile
from units.models import Unit
from users.models import TruffeUser

import datetime
import json
import pytz
import sys
import os


class Command(BaseCommand):
    """ Requirements : files in /media/uploads/_generic/Subvention/"""

    help = 'Import subventions'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        paris_tz = pytz.timezone("Europe/Paris")

        root_user = TruffeUser.objects.get(username=179189)

        for subvention_data in data['data']:
            (unit, blank_unit_name) = (None, None)

            try:
                if subvention_data['groupe_name']:
                    unit = Unit.objects.get(name=subvention_data['groupe_name'])
                else:
                    blank_unit_name = subvention_data['forWho']
                unit_name = blank_unit_name or unit.name
            except:
                print u"Unit not found !!", subvention_data['groupe_name'], subvention_data['forWho']
                unit_name = None

            if unit_name:
                try:
                    user = TruffeUser.objects.get(username=subvention_data['contact_username'])
                except:
                    user = root_user

                try:
                    ay = AccountingYear.objects.get(name=subvention_data['year_name'])
                except:
                    ay = None

                if ay:
                    subv, created = Subvention.objects.get_or_create(name=u"{} {}".format(unit_name, ay.name), unit=unit, unit_blank_name=blank_unit_name, accounting_year=ay, amount_asked=subvention_data['amount_asked'],
                        amount_given=subvention_data['amount_given'], mobility_asked=subvention_data['mobility_asked'], mobility_given=subvention_data['mobility_given'], description=subvention_data['description'])

                    if subvention_data['traitee']:
                        subv.status = '2_treated'
                    elif subvention_data['deposee']:
                        subv.status = '1_submited'
                    subv.save()

                    if created:
                        SubventionLogging(who=user, what='imported', object=subv).save()
                        print "+ {!r}".format(subv.name)

                    order = 0
                    for line_data in subvention_data['lines']:
                        if line_data['name']:
                            if line_data['date'] == 'None':
                                line_data['date'] = '1970-01-01'
                            start_date = paris_tz.localize(datetime.datetime.strptime(line_data['date'], '%Y-%m-%d'))
                            subvline, created = SubventionLine.objects.get_or_create(subvention=subv, name=line_data['name'], start_date=start_date, end_date=start_date, nb_spec=0, order=order)
                            if created:
                                print "  + {!r}".format(subvline.name)
                            order += 1

                    for file_data in subvention_data['uploads']:
                        if not os.path.isfile(os.path.join('uploads', '_generic', 'Subvention', file_data.split('/')[-1])):
                            print "   (!) Missing file {}".format(file_data)
                        else:
                            __, created = SubventionFile.objects.get_or_create(uploader=user, object=subv, file=os.path.join('uploads', '_generic', 'Subvention', file_data.split('/')[-1]), defaults={'upload_date': now()})
                            if created:
                                print "  (L)", file_data
