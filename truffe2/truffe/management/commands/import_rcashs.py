# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from accounting_core.models import CostCenter, AccountingYear
from accounting_tools.models import Withdrawal, WithdrawalFile, WithdrawalLogging, LinkedInfo
from users.models import TruffeUser

import json
import os
import sys


class Command(BaseCommand):
    """ Requirements : files in /media/uploads/_generic/Withdrawal/"""

    help = 'Import retraits cash'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        root_user = TruffeUser.objects.get(username=179189)
        withdrawal_ct = ContentType.objects.get(app_label="accounting_tools", model="withdrawal")
        status_mapping = {'1': '0_draft', '2': '1_agep_validable', '3': '2_withdrawn', '4': '4_archived'}

        for rcash_data in data['data']:
            try:
                ay = AccountingYear.objects.get(name=rcash_data['accounting_year__name'])
            except:
                print u"AccountingYear not found !!", rcash_data['accounting_year__name']
                ay = None

            if ay:
                try:
                    costcenter = CostCenter.objects.get(account_number=rcash_data['costcenter__account_number'], accounting_year=ay)
                except:
                    print u"CostCenter not found !!", rcash_data['costcenter__account_number']
                    costcenter = None

                if costcenter:
                    try:
                        user = TruffeUser.objects.get(username=rcash_data['creator_username'])
                    except:
                        user = root_user

                    if rcash_data['withdrawn_date'] == "None":
                        rcash_data['withdrawn_date'] = rcash_data['desired_date']  # Histoire de fixer le problème salement

                    rcash, created = Withdrawal.objects.get_or_create(unit=costcenter.unit, costcenter=costcenter, accounting_year=ay, status=status_mapping[rcash_data['status']],
                        amount=rcash_data['amount'], description=rcash_data['description'], desired_date=rcash_data['desired_date'], withdrawn_date=rcash_data['withdrawn_date'])

                    if created:
                        while Withdrawal.objects.filter(name=rcash_data['name']).exists():
                            rcash_data['name'] += '*'
                        rcash.name = rcash_data['name']
                        rcash.save()
                        WithdrawalLogging(who=user, what='imported', object=rcash).save()
                        print "+ ", rcash.name

                    if rcash_data['linked_info']:
                        linked, created = LinkedInfo.objects.get_or_create(object_id=rcash.pk, content_type=withdrawal_ct, **rcash_data['linked_info'])
                        if created:
                            print "  (I)", linked.first_name, linked.last_name

                    for file_data in rcash_data['uploads']:
                            __, created = WithdrawalFile.objects.get_or_create(uploader=user, object=rcash, file=os.path.join('uploads', '_generic', 'Withdrawal', file_data.split('/')[-1]), defaults={'upload_date': now()})
                            if created:
                                print "  (L)", file_data
