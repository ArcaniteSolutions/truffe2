# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from accounting_core.models import CostCenter, AccountingYear, Account
from accounting_tools.models import CashBook, CashBookFile, CashBookLine, CashBookLogging, LinkedInfo, Withdrawal
from app.ldaputils import get_attrs_of_sciper
from truffe.models import ImportedCreditCard
from users.models import TruffeUser


import datetime
import json
import pytz
import os
import sys


class Command(BaseCommand):
    """ Requirements : files in /media/uploads/_generic/CashBook/"""

    help = 'Import journaux de caisse'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        paris_tz = pytz.timezone("Europe/Paris")
        root_user = TruffeUser.objects.get(username=179189)
        cashbook_ct = ContentType.objects.get(app_label="accounting_tools", model="cashbook")
        status_mapping = {'1': '0_draft', '2': '1_unit_validable', '3': '4_archived'}
        helper_mapping = {1: '0_withdraw', 2: '1_deposit', 3: '2_sell', 4: '4_buy', 5: '3_invoice', 6: '6_input', 7: '7_output', 8: '5_reimburse'}

        for jdc_data in data['data']:
            try:
                ay = AccountingYear.objects.get(name=jdc_data['accounting_year__name'])
            except:
                print u"AccountingYear not found !!", jdc_data['accounting_year__name']
                ay = None

            if ay:
                try:
                    costcenter = CostCenter.objects.get(account_number=jdc_data['costcenter__account_number'], accounting_year=ay)
                except:
                    print u"CostCenter not found !!", jdc_data['costcenter__account_number']
                    costcenter = None

                if costcenter:
                    try:
                        if jdc_data['creator_username'] is None:
                            jdc_data['creator_username'] = 195835
                        user = TruffeUser.objects.get(username=jdc_data['creator_username'])
                    except TruffeUser.DoesNotExist:
                        print "Creation of user {!r}".format(jdc_data['creator_username'])
                        user = TruffeUser(username=jdc_data['creator_username'], is_active=True)
                        user.last_name, user.first_name, user.email = get_attrs_of_sciper(jdc_data['creator_username'])
                        user.save()
                    except Exception as e:
                        print "user is root_user", e
                        user = root_user

                    jdc, created = CashBook.objects.get_or_create(costcenter=costcenter, accounting_year=ay, user=user, status=status_mapping[jdc_data['status']],
                                                                  comment=jdc_data['commentaire'], name=jdc_data['name'], nb_proofs=jdc_data['nb_just'])

                    if created:
                        CashBookLogging(who=user, what='imported', object=jdc).save()
                        print "+ {!r}".format(jdc.name)

                    if jdc_data['linked_info']:
                        try:
                            linked, created = LinkedInfo.objects.get_or_create(object_id=jdc.pk, content_type=cashbook_ct, user_pk=user.pk, **jdc_data['linked_info'])
                            if created:
                                print "  (I) {!r} {!r}".format(linked.first_name, linked.last_name)
                        except Exception as e:
                            print e
                            print u"LinkedInfo not found !!", jdc_data['linked_info']

                    if jdc_data['rcash']:
                        try:
                            withdrawal = Withdrawal.objects.get(**jdc_data['rcash'])
                            if jdc.proving_object != withdrawal:
                                jdc.proving_object = withdrawal
                                jdc.save()
                                print "  (R) {!r}".format(withdrawal.name)
                        except:
                            print u"Rcash not found !! {!r}".format(jdc_data['rcash'])

                    if jdc_data['credit_card']:
                        try:
                            creditcard = ImportedCreditCard.objects.get(**jdc_data['credit_card'])
                            jdc.proving_object = creditcard
                            jdc.save()
                            print "  (C) {!r}".format(creditcard.name)
                        except:
                            print u"Creditcard not found !! {!r}".format(jdc_data['credit_card'])

                    for line_data in jdc_data['lines']:
                        try:
                            account = Account.objects.get(account_number=line_data['account__account_number'], accounting_year=ay)
                            date = paris_tz.localize(datetime.datetime.strptime(line_data['date'], '%Y-%m-%d'))
                            __, created = CashBookLine.objects.get_or_create(cashbook=jdc, label=line_data['name'], proof=line_data['just'],
                                                                             account=account, order=line_data['order'],
                                                                             value=line_data['amount'], value_ttc=line_data['amount'], tva=0, date=date, helper=helper_mapping[line_data['help']])
                            if created:
                                print "  (+) {!r}".format(line_data['name'])
                        except:
                            print u"Account not found !! {!r}".format(line_data['account__account_number'])

                    for file_data in jdc_data['uploads']:

                        if not os.path.isfile(os.path.join('media', 'uploads', '_generic', 'CashBook', file_data.split('/')[-1])):
                            print "   (!) Missing file {}".format(file_data)
                        else:
                            __, created = CashBookFile.objects.get_or_create(uploader=user, object=jdc, file=os.path.join('uploads', '_generic', 'CashBook', file_data.split('/')[-1]), defaults={'upload_date': now()})
                            if created:
                                print "  (L) {!r}".format(file_data)
