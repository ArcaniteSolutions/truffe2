# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.encoding import smart_str
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db import connections
from django.core.paginator import InvalidPage, EmptyPage, Paginator, PageNotAnInteger
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.db.models import Q
from django.utils.html import strip_tags


import uuid
import datetime
import time
import collections
import decimal
import json


from notifications.utils import notify_people


@login_required
def accounting_graph(request):

    from accounting_core.models import CostCenter
    from accounting_main.models import AccountingLine

    costcenter = get_object_or_404(CostCenter, pk=request.GET.get('costcenter'))

    if not AccountingLine.static_rights_can('LIST', request.user, costcenter.unit, costcenter.accounting_year):
        raise Http404

    data = collections.OrderedDict()

    for line in AccountingLine.objects.filter(costcenter=costcenter).order_by('date'):
        timestamp = int((time.mktime(line.date.timetuple()) + 3600) * 1000)
        data[timestamp] = -line.current_sum

    return render(request, 'accounting_main/accountingline/graph.html', {'costcenter': costcenter, 'random': str(uuid.uuid4()), 'data': data})


@login_required
def errors_send_message(request, pk):
    from accounting_main.models import AccountingError, AccountingErrorMessage

    error = get_object_or_404(AccountingError, pk=pk)

    if not error.rights_can('ADD_COMMENT', request.user):
        raise Http404

    AccountingErrorMessage(author=request.user, message=request.POST.get('message'), error=error).save()

    notify_people(request, u'AccountingError.{}.message'.format(error.unit), 'accounting_error_message', error, error.build_group_members_for_compta_everyone_with_messages(), {'message': request.POST.get('message')})

    messages.success(request, _(u'Message ajouté !'))

    return HttpResponse('')


@login_required
def accounting_import_step0(request):
    """Phase 0 de l'import: Crée une nouvelle session d'import"""

    from accounting_main.models import AccountingLine

    if not AccountingLine.static_rights_can('IMPORT', request.user):
        raise Http404

    key = str(uuid.uuid4())
    session_key = 'T2_ACCOUNTING_IMPORT_{}'.format(key)

    request.session[session_key] = {'is_valid': True, 'has_data': False}

    return redirect('accounting_main.views.accounting_import_step1', key)


def _get_import_session_data(request, key):

    from accounting_main.models import AccountingLine

    if not AccountingLine.static_rights_can('IMPORT', request.user):
        raise Http404

    session_key = 'T2_ACCOUNTING_IMPORT_{}'.format(key)

    session_data = request.session.get(session_key)

    if not session_data or not session_data['is_valid']:
        messages.warning(request, _(u'Session d\'importation invalide.'))
        return (None, redirect('accounting_main.views.accounting_import_step0'))

    return (session_key, session_data)


def _csv_2014_processor(file):

    def unicode_csv_reader(unicode_csv_data, *args, **kwargs):

        import csv

        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(unicode_csv_data, *args, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            yield [unicode(cell, 'iso8859') for cell in row]

    with open(file, 'rb') as csvfile:

        spamreader = unicode_csv_reader(csvfile, 'excel-tab')

        if spamreader.next()[0] != 'Extrait CdC':
            messages.warning(request, "L'header initial ne correspond pas ({} vs {})".format(spamreader.next()[0], 'Extrait CdC'))
            return False

        current_costcenter = None
        phase_header = False
        phase_solde = False
        phase_compte = False

        current_line = spamreader.next()

        wanted_lines = []

        order = 0

        while True:

            if current_line:

                if current_costcenter:
                    if current_line[0]:

                        cDate = current_line[0]
                        cNoPiece = current_line[1]
                        cTexte = current_line[2]
                        cCompte = current_line[3]
                        cDebit = current_line[4]
                        cCredit = current_line[5]
                        cSituation = current_line[6]
                        sCygne = current_line[7]
                        cOrigine = ''
                        cTva = 0.0

                        if not cDebit:
                            cDebit = 0.0
                        else:
                            cDebit = float(cDebit.replace('\'', ''))

                        if not cCredit:
                            cCredit = 0.0
                        else:
                            cCredit = float(cCredit.replace('\'', ''))

                        if not cSituation or cSituation == '-':
                            cSituation = 0.0
                        else:
                            cSituation = float(cSituation.replace('\'', ''))

                        if sCygne == '-':
                            cSituation *= -1

                        cDate2 = cDate.split('.')

                        wanted_lines.append({
                            'costcenter': current_costcenter,
                            'date': cDate2[2] + '-' + cDate2[1] + '-' + cDate2[0],
                            'account': cCompte,
                            'text': cTexte,
                            'output': float(cDebit),
                            'input': float(cCredit),
                            'current_sum': float(cSituation),
                            'tva': str(cTva),
                            'order': order,
                            'document_id': cNoPiece,
                        })

                        order += 1

                    elif current_line[2] == 'Total':
                        current_costcenter = None
                    else:
                        messages.warning(request, u"Ligne étrange: {}".format(current_line))
                        return False

                elif phase_header:

                    phase_header = False

                    excepted_line = [u'Date', u'Pi\xe8ce', u"Texte d'\xe9criture", u'Type C.', u'D\xe9bit CHF', u'Cr\xe9dit CHF', u'Courant ']

                    if current_line != excepted_line:
                        messages.warning(request, "L'header de début de lignes ne corespond pas ({} vs {})".format(current_line, excepted_line))
                        return False
                    else:
                        phase_solde = True

                elif phase_solde:

                    phase_solde = False

                    excepted_line = [u'Solde CHF', u'']

                    if current_line != excepted_line:
                        messages.warning(request, "L'header de fin de lignes ne corespond pas ({} vs {})".format(current_line, excepted_line))
                        return False
                    else:
                        phase_compte = True

                elif phase_compte:

                    phase_compte = False

                    current_costcenter = current_line[0].split()[0].strip()

                    order = 0

                elif current_line[0] == 'CdC':
                    phase_header = True
                else:
                    pass

            try:
                current_line = spamreader.next()
            except StopIteration:
                return wanted_lines

    return wanted_lines


def _diff_generator(year, data):

    from accounting_main.models import AccountingLine
    from accounting_core.models import CostCenter, Account

    valids_ids = []

    to_add = []
    nop = []
    to_update = []

    for wanted_line in data:

        try:
            costcenter = CostCenter.objects.get(accounting_year=year, account_number=wanted_line['costcenter'])
        except CostCenter.DoesNotExist:
            messages.warning(request, "Le centre de coûts {} n'existe pas !".format(wanted_line['costcenter']))
            return False

        try:
            account = Account.objects.get(accounting_year=year, account_number=wanted_line['account'])
        except CostCenter.DoesNotExist:
            messages.warning(request, "Le compte de CG {} n'existe pas !".format(wanted_line['account']))
            return False

        line = AccountingLine.objects.filter(unit=costcenter.unit, account=account, costcenter=costcenter, date=wanted_line['date'], tva=wanted_line['tva'], text=wanted_line['text'], output=wanted_line['output'], input=wanted_line['input'], document_id=wanted_line['document_id'], deleted=False, accounting_year=year).exclude(pk__in=valids_ids).first()

        if line:

            diffs = {}

            fields_to_check = ['order', 'current_sum', ]

            for field in fields_to_check:

                v = getattr(line, field)

                if isinstance(v, decimal.Decimal):
                    v = float(v)
                    wanted_line[field] = float(wanted_line[field])

                if v != wanted_line[field]:
                    diffs[field] = (v, wanted_line[field])

            if diffs:
                to_update.append((line.pk, wanted_line, diffs))
            else:
                nop.append(line.pk)

            valids_ids.append(line.pk)
        else:
            to_add.append(wanted_line)

    to_delete = map(lambda line: line.pk, AccountingLine.objects.filter(accounting_year=year).exclude(pk__in=valids_ids))

    return {'to_add': to_add, 'to_update': to_update, 'nop': nop, 'to_delete': to_delete}


@login_required
def accounting_import_step1(request, key):

    (session_key, session_data) = _get_import_session_data(request, key)

    if not session_key:
        return session_data  # ...

    if session_data['has_data']:
        return redirect('accounting_main.views.accounting_import_step2', key)

    from accounting_main.forms2 import ImportForm

    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)

        if form.is_valid():
            file_key = '/tmp/truffe_import_{}_data.file'.format(key)
            with open(file_key, 'wb+') as destination:
                for chunk in request.FILES['file'].chunks():
                    destination.write(chunk)

            if form.cleaned_data['type'] == 'csv_2014':
                wanted_data = _csv_2014_processor(file_key)

                if wanted_data:
                    diff = _diff_generator(form.cleaned_data['year'], wanted_data)

                    if diff:

                        session_data['data'] = diff
                        session_data['year'] = form.cleaned_data['year'].pk
                        session_data['has_data'] = True

                        request.session[session_key] = session_data
                        return redirect('accounting_main.views.accounting_import_step2', key)

    else:
        form = ImportForm()

    return render(request, "accounting_main/import/step1.html", {'key': key, 'form': form})


@login_required
def accounting_import_step2(request, key):

    from accounting_main.models import AccountingLine, AccountingLineLogging
    from accounting_core.models import AccountingYear, CostCenter, Account

    (session_key, session_data) = _get_import_session_data(request, key)

    if not session_key:
        return session_data  # ...

    if not session_data['has_data']:
        return redirect('accounting_main.views.accounting_import_step1', key)

    year = get_object_or_404(AccountingYear, pk=session_data['year'])

    # Map line id to have lines (efficentily)
    line_cache = {}
    for line in AccountingLine.objects.filter(accounting_year=year, deleted=False):
        line_cache[line.pk] = line

    diff = session_data['data']

    diff['nop'] = map(lambda line_pk: line_cache[line_pk], diff['nop'])
    diff['to_delete'] = map(lambda line_pk: line_cache[line_pk], diff['to_delete'])
    diff['to_update'] = map(lambda (line_pk, __, ___): (line_cache[line_pk], __, ___), diff['to_update'])

    if request.method == 'POST':

        for wanted_line in diff['to_add']:
            # NB: Si quelqu'un modifie les trucs pendant l'import, ça pétera.
            # C'est ultra peut proptable, donc ignoré
            costcenter = CostCenter.objects.get(accounting_year=year, account_number=wanted_line['costcenter'])
            account = Account.objects.get(accounting_year=year, account_number=wanted_line['account'])

            line = AccountingLine(unit=costcenter.unit, account=account, costcenter=costcenter, date=wanted_line['date'], tva=wanted_line['tva'], text=wanted_line['text'], output=wanted_line['output'], input=wanted_line['input'], document_id=wanted_line['document_id'], deleted=False, accounting_year=year, current_sum=wanted_line['current_sum'], order=wanted_line['order'])
            line.save()
            AccountingLineLogging(object=line, who=request.user, what='created').save()

        for line, wanted_line, diffs in diff['to_update']:

            for field, (old, new) in diffs.iteritems():
                setattr(line, field, new)

            line.save()
            AccountingLineLogging(object=line, who=request.user, what='edited', extra_data=json.dumps({'added': None, 'edited': diffs, 'deleted': None})).save()

        for line in diff['to_delete']:
            for error in line.accountingerror_set.all():
                error.linked_line = None
                error.save()
            line.delete()  # harddelete.

        request.session[session_key] = {}
        messages.success(request, _(u"Compta importée !"))
        return redirect('accounting_main.views.accounting_import_step0')

    return render(request, "accounting_main/import/step2.html", {'key': key, 'diff': diff})
