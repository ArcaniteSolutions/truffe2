# -*- coding: utf-8 -*-

from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from accounting_core.models import AccountingYear, Account, AccountCategory, CostCenter
from units.models import Unit

import datetime
import pytz
import json
import sys


class Command(BaseCommand):
    help = 'Import financesglob'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())
        mainant = now()


        paris_tz = pytz.timezone("Europe/Paris")

        for year_data in data['year']:
            ay, created = AccountingYear.objects.get_or_create(name=year_data['name'])
            ay.status = '3_archived'
            years = ay.name.split('-')
            ay.start_date = paris_tz.localize(datetime.datetime.strptime('{}-08-01 00:00:00'.format(years[0]), '%Y-%m-%d %H:%M:%S'))
            ay.end_date = paris_tz.localize(datetime.datetime.strptime('{}-08-01 00:00:00'.format(years[1]), '%Y-%m-%d %H:%M:%S')) - datetime.timedelta(seconds=1)

            if mainant < ay.end_date and mainant > ay.start_date:
                ay.status = '1_active'

            ay.save()
            if created:
                print "(+)", ay

            for tcb_data in data['typeCompteBilan']:
                ac, created = AccountCategory.objects.get_or_create(name=tcb_data['name'], description=tcb_data['description'], accounting_year=ay)

                if created:
                    print "  (+)", ac

                for ct_data in tcb_data['compte_types']:
                    sub_ac, created = AccountCategory.objects.get_or_create(name=ct_data['name'], description=ct_data['description'], parent_hierarchique=ac, accounting_year=ay)

                    if created:
                        print "    (+)", sub_ac

            print "*" * 20

            for num_data in year_data['numeros']:
                try:
                    unit = Unit.objects.get(name=num_data['unit_name'])
                except:
                    unit = Unit.objects.get(pk=1)
                    print u"Cost Center {!r} from Year {!r} has no Unit. Set to Comité de Direction. Edit manually?".format(num_data['name'], ay)

                cc, created = CostCenter.objects.get_or_create(name=num_data['name'], account_number=num_data['account_number'], description=num_data['description'], accounting_year=ay, defaults={'unit': unit})
                cc.save()

                if created:
                    print "  (+)", cc

            print "*" * 20

            for cc_data in year_data['compte_cats']:
                try:
                    parent = AccountCategory.objects.get(accounting_year=ay, name=cc_data['compte_type_name'])
                    leaf_ac, created = AccountCategory.objects.get_or_create(name=cc_data['name'], parent_hierarchique=parent, accounting_year=ay)

                    if created:
                        print "  (+)", leaf_ac
                except:
                    print "Parent not found !!"

                for comp_data in cc_data['comptes']:
                    try:
                        acc, created = Account.objects.get_or_create(name=comp_data['name'], account_number=comp_data['account_number'], description=comp_data['description'], category=leaf_ac, accounting_year=ay)
                        if comp_data['ndfComs']:
                            acc.visibility = 'all'
                        elif comp_data['ndfMaster']:
                            acc.visibility = 'cdd'
                        else:
                            acc.visibility = 'root'

                        acc.save()
                        if created:
                            print "    (+)", acc
                    except IntegrityError:
                        print u"Duplicate with name {!r} number {!r} and year {!r}".format(acc.name, acc.account_number, ay)
