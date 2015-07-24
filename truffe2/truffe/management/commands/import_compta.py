# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from accounting_core.models import CostCenter, AccountingYear, Account
from accounting_main.models import AccountingLine, AccountingLineLogging, AccountingError, AccountingErrorLogging
from users.models import TruffeUser

import json
import os
import sys
import datetime
import pytz


class Command(BaseCommand):
    help = 'Import compta'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        root_user = TruffeUser.objects.get(username=185952)
        paris_tz = pytz.timezone("Europe/Paris")
        status_mapping = {'wai': '0_imported', 'oky': '1_validated', 'err': '2_error'}

        line_mapping = {}

        for line_data in data['lignes']:

            try:
                ay = AccountingYear.objects.get(name=line_data['year'])
            except:
                print u"AccountingYear not found !!", line_data['year']
                ay = None

            if ay:
                try:
                    costcenter = CostCenter.objects.get(account_number=line_data['numero'], accounting_year=ay)
                except:
                    print u"CostCenter not found !!", line_data['numero']
                    costcenter = None

                if costcenter:

                    try:
                        account = Account.objects.get(account_number=line_data['compte'], accounting_year=ay)
                    except:
                        print u"Account not found !!", line_data['compte']
                        account = None

                    if account:

                        date = paris_tz.localize(datetime.datetime.strptime(line_data['date'], '%Y-%m-%d'))
                        line, created = AccountingLine.objects.get_or_create(unit=costcenter.unit, costcenter=costcenter, accounting_year=ay, status=status_mapping[line_data['status']], account=account, date=date, tva=0, text=line_data['texte'], output=line_data['debit'], input=line_data['credit'], current_sum=line_data['situation'])

                        print "(+/", created, ")", line

                        if created:
                            AccountingLineLogging(object=line, who=root_user, what='created').save()

                        line_mapping[line_data['pk']] = line

        for error_data in data['errors']:

            try:
                ay = AccountingYear.objects.get(name=error_data['year'])
            except:
                print u"AccountingYear not found !!", error_data['year']
                ay = None

            if ay:
                try:
                    costcenter = CostCenter.objects.get(account_number=error_data['numero'], accounting_year=ay)
                except:
                    print u"CostCenter not found !!", error_data['numero']
                    costcenter = None

                if costcenter:
                    date = paris_tz.localize(datetime.datetime.strptime(error_data['date'], '%Y-%m-%d %H:%M:%S'))

                    if error_data['ligne']:
                        line = line_mapping[error_data['ligne']]
                    else:
                        line = None

                    error, created = AccountingError.objects.get_or_create(unit=costcenter.unit, costcenter=costcenter, accounting_year=ay, status='0_drafting', linked_line=line, initial_remark=error_data['texte'])

                    try:
                        user = TruffeUser.objects.get(username=error_data['creator'])
                    except:
                        print "(!) User not found", error_data['creator']
                        user = root_user

                    print "(+/", created, ")", error

                    if created:
                        ael = AccountingErrorLogging(object=error, who=user, when=date, what='created')
                        ael.save()
                        # Hack pour forcer la date
                        ael.when = date
                        ael.save()
