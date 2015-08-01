# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from accounting_core.models import CostCenter, AccountingYear
from users.models import TruffeUser
from truffe.models import ImportedCreditCard

import json
import sys


class Command(BaseCommand):
    help = 'Import creditcard'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        root_user = TruffeUser.objects.get(username=179189)

        for cc_data in data['data']:
            try:
                name = cc_data.pop('accounting_year__name')
                ay = AccountingYear.objects.get(name=name)
            except:
                print u"AccountingYear not found !!", name
                ay = None

            if ay:
                try:
                    account_number = cc_data.pop('costcenter__account_number')
                    costcenter = CostCenter.objects.get(account_number=account_number, accounting_year=ay)
                except:
                    print u"CostCenter not found !!", account_number
                    costcenter = None

                if costcenter:
                    try:
                        username = cc_data.pop('creator_username')
                        user = TruffeUser.objects.get(username=username)
                    except:
                        user = root_user

                    cc_name = cc_data.pop('name')
                    cc_data['defaults'] = {'costcenter_id': costcenter.pk, 'accounting_year_id': ay.pk, 'user': user}
                    cc, created = ImportedCreditCard.objects.get_or_create(**cc_data)

                    if created:
                        while ImportedCreditCard.objects.filter(name=cc_name).exists():
                            cc_name += '*'
                        cc.name = cc_name
                        cc.save()

                        print "+ {!r}".format(cc.name)
