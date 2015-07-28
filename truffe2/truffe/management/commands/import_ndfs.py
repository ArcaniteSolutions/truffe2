# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from accounting_core.models import CostCenter, AccountingYear, Account
from accounting_tools.models import ExpenseClaim, ExpenseClaimFile, ExpenseClaimLine, ExpenseClaimLogging, LinkedInfo
from app.ldaputils import get_attrs_of_sciper
from users.models import TruffeUser

import json
import os
import sys


class Command(BaseCommand):
    """ Requirements : files in /media/uploads/_generic/ExpenseClaim/"""

    help = 'Import notes de frais'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        root_user = TruffeUser.objects.get(username=179189)
        expenseclaim_ct = ContentType.objects.get(app_label="accounting_tools", model="expenseclaim")
        status_mapping = {'1': '0_draft', '2': '2_agep_validable', '3': '4_archived'}

        for ndf_data in data['data']:
            try:
                ay = AccountingYear.objects.get(name=ndf_data['accounting_year__name'])
            except:
                print u"AccountingYear not found !!", ndf_data['accounting_year__name']
                ay = None

            if ay:
                try:
                    costcenter = CostCenter.objects.get(account_number=ndf_data['costcenter__account_number'], accounting_year=ay)
                except:
                    print u"CostCenter not found !!", ndf_data['costcenter__account_number']
                    costcenter = None

                if costcenter:
                    try:
                        user = TruffeUser.objects.get(username=ndf_data['creator_username'])
                    except TruffeUser.DoesNotExist:
                        print "Creation of user {!r}".format(ndf_data['creator_username'])
                        user = TruffeUser(username=ndf_data['creator_username'], is_active=True)
                        user.last_name, user.first_name, user.email = get_attrs_of_sciper(ndf_data['creator_username'])
                        user.save()
                    except Exception as e:
                        print "user is root_user", e
                        user = root_user

                    ndf, created = ExpenseClaim.objects.get_or_create(unit=costcenter.unit, costcenter=costcenter, accounting_year=ay, user=user, status=status_mapping[ndf_data['status']],
                                                                      comment=ndf_data['commentaire'], name=ndf_data['name'], nb_proofs=ndf_data['nb_just'])

                    if created:
                        ExpenseClaimLogging(who=user, what='imported', object=ndf).save()
                        print "+ {!r}".format(ndf.name)

                    if ndf_data['linked_info']:
                        linked, created = LinkedInfo.objects.get_or_create(object_id=ndf.pk, content_type=expenseclaim_ct, user_pk=user.pk, **ndf_data['linked_info'])
                        if created:
                            print "  (I) {!r} {!r}".format(linked.first_name, linked.last_name)

                    for line_data in ndf_data['lines']:
                        account = Account.objects.get(account_number=line_data['account__account_number'], accounting_year=ay)
                        __, created = ExpenseClaimLine.objects.get_or_create(expense_claim=ndf, label=line_data['name'], account=account, proof=line_data['just'],
                                                                             order=line_data['order'], value=line_data['amount'], value_ttc=line_data['amount'], tva=0)
                        if created:
                            print "  (+) {!r}".format(line_data['name'])

                    for file_data in ndf_data['uploads']:
                        print file_data
                        __, created = ExpenseClaimFile.objects.get_or_create(uploader=user, object=ndf, file=os.path.join('uploads', '_generic', 'ExpenseClaim', file_data.split('/')[-1]), defaults={'upload_date': now()})
                        if created:
                            print "  (L) {!r}".format(file_data)
