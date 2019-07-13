# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse
from django.utils.timezone import now
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.conf import settings


import csv, codecs, cStringIO
import os
import json
from PIL import Image


from app.utils import generate_pdf


def get_statistics(subventions):
    """Given a set of subventions, return statistics about comms and assocs."""
    assoc = subventions.filter(unit=None, deleted=False).aggregate(Sum('amount_asked'), Sum('amount_given'), Sum('mobility_asked'), Sum('mobility_given'))
    comms = subventions.exclude(unit=None).filter(deleted=False).aggregate(Sum('amount_asked'), Sum('amount_given'), Sum('mobility_asked'), Sum('mobility_given'))

    return {'asso_amount_asked': assoc['amount_asked__sum'], 'asso_amount_given': assoc['amount_given__sum'],
            'asso_mobility_asked': assoc['mobility_asked__sum'], 'asso_mobility_given': assoc['mobility_given__sum'],
            'comm_amount_asked': comms['amount_asked__sum'], 'comm_amount_given': comms['amount_given__sum'],
            'comm_mobility_asked': comms['mobility_asked__sum'], 'comm_mobility_given': comms['mobility_given__sum']}


@login_required
def export_demands_yearly(request, ypk):
    from accounting_core.models import AccountingYear
    from accounting_tools.models import Subvention

    if not Subvention.static_rights_can('EXPORT', request.user):
        raise Http404

    try:
        ay = AccountingYear.objects.get(pk=ypk)
        subventions = Subvention.objects.filter(accounting_year=ay, deleted=False).order_by('unit__name', 'unit_blank_name')
        if subventions:
            subventions = list(subventions) + [get_statistics(subventions)]
        subv = [(ay.name, subventions)]
    except AccountingYear.DoesNotExist:
        subv = [(_(u'Période inconnue'), Subvention.objects.none())]

    return generate_pdf("accounting_tools/subvention/subventions_pdf.html", request, {'subventions': subv})


@login_required
def export_all_demands(request):
    from accounting_core.models import AccountingYear
    from accounting_tools.models import Subvention

    if not Subvention.static_rights_can('EXPORT', request.user):
        raise Http404

    years = AccountingYear.objects.filter(deleted=False).order_by('start_date')
    subventions = []
    for ay in years:
        subv = Subvention.objects.filter(accounting_year=ay, deleted=False).order_by('unit__name', 'unit_blank_name')
        if subv:
            subv = list(subv) + [get_statistics(subv)]
        subventions.append((ay.name, subv))

    summary = []
    units = sorted(list(set(map(lambda subv: subv.get_real_unit_name(), list(Subvention.objects.all())))))
    for unit_name in units:
        line = [unit_name]
        for year in years:
            year_subv = Subvention.objects.filter(accounting_year=year, deleted=False).filter(Q(unit__name=unit_name) | Q(unit_blank_name=unit_name)).first()
            if year_subv:
                line += [year_subv.amount_asked, year_subv.amount_given, year_subv.mobility_asked, year_subv.mobility_asked]
            else:
                line += ["", "", "", ""]
        summary.append(line)

    return generate_pdf("accounting_tools/subvention/subventions_pdf.html", request, {'subventions': subventions, 'summary': summary, 'years': years})


@login_required
def invoice_pdf(request, pk):

    from accounting_tools.models import Invoice

    invoice = get_object_or_404(Invoice, pk=pk, deleted=False)

    if not invoice.rights_can('SHOW', request.user):
        raise Http404

    img = invoice.generate_bvr()
    img = img.resize((1414, 1000), Image.LANCZOS)
    img.save(os.path.join(settings.MEDIA_ROOT, 'cache/bvr/{}.png').format(invoice.pk))

    return generate_pdf("accounting_tools/invoice/pdf.html", request, {'invoice': invoice})


@login_required
def invoice_bvr(request, pk):

    from accounting_tools.models import Invoice

    invoice = get_object_or_404(Invoice, pk=pk, deleted=False)

    if not invoice.rights_can('SHOW', request.user):
        raise Http404

    img = invoice.generate_bvr()

    response = HttpResponse(mimetype="image/png")
    img.save(response, 'png')
    return response


@login_required
def withdrawal_pdf(request, pk):

    from accounting_tools.models import Withdrawal

    withdrawal = get_object_or_404(Withdrawal, pk=pk, deleted=False)

    if not withdrawal.rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/withdrawal/pdf.html", request, {'object': withdrawal})


@login_required
def internaltransfer_pdf(request, pk):
    from accounting_tools.models import InternalTransfer

    transfers = [get_object_or_404(InternalTransfer, pk=pk_, deleted=False) for pk_ in filter(lambda x: x, pk.split(','))]
    transfers = filter(lambda tr: tr.rights_can('SHOW', request.user), transfers)

    if not transfers:
        raise Http404
    elif len(transfers) == 1:
        return generate_pdf("accounting_tools/internaltransfer/single_pdf.html", request, {'object': transfers[0]})
    else:
        return generate_pdf("accounting_tools/internaltransfer/multiple_pdf.html", request, {'objects': transfers})

@login_required
def internaltransfer_csv(request, pk):
    from accounting_tools.models import InternalTransfer
    from accounting_core.models import TVA
    import datetime

    transfers = [get_object_or_404(InternalTransfer, pk=pk_, deleted=False) for pk_ in filter(lambda x: x, pk.split(','))]
    transfers = filter(lambda tr: tr.rights_can('SHOW', request.user), transfers)
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    if len(transfers) == 1:
        response['Content-Disposition'] = 'attachment; filename="'+slugify(transfers[0].name)+'.csv"'
    else:
        response['Content-Disposition'] = 'attachment; filename="internal_transfers_'+datetime.date.today().strftime("%d-%m-%Y")+'.csv"'
    #L'écriture du csv permet l'import dans sage comme définit ici : https://onlinehelp.sageschweiz.ch/sage-start/fr-ch/content/technique/d%C3%A9finition%20de%20l%20interface.htm
    #We still need to add costcenters (and modify the sage import interface)
    writer = UnicodeCSVWriter(response)
    
    for transfer in transfers:
        try: 
            tva = TVA.objects.get(value=0)
        except:
            tva = TVA()
            tva.code = ''
            tva.value = 0
        header_row = [u'0',transfer.pk,'','',transfer.name, transfer.amount, transfer.amount, '', '', 0, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',u'INT_TF#'+unicode(transfer.pk)]
        debit_row  = [u'1','','','','','','','','','','','',u'1',transfer.pk,transfer.account.account_number,u'CHF',transfer.name+u' - Débit',transfer.amount, tva.code, tva.value, '', u'Non Soumis à la TVA' , u'Débit' ,'',transfer.transfert_date.strftime(u"%d.%m.%Y"),0,transfer.amount,transfer.amount,0,u'INT_TF#'+unicode(transfer.pk)] #need to put transfer.cost_center_from.account_number somewhere
        credit_row = [u'2','','','','','','','','','','','',u'2',transfer.pk,transfer.account.account_number,u'CHF',transfer.name+u' - Crédit',transfer.amount, tva.code, tva.value, '', u'Non Soumis à la TVA' , u'Crédit' ,'',transfer.transfert_date.strftime(u"%d.%m.%Y"),0,transfer.amount,transfer.amount,0,u'INT_TF#'+unicode(transfer.pk)]  #need to put transfer.cost_center_to.account_number somewhere
        writer.writerows([header_row, debit_row, credit_row])
    return response

@login_required
def expenseclaim_pdf(request, pk):
    from accounting_tools.models import ExpenseClaim

    expenseclaim = get_object_or_404(ExpenseClaim, pk=pk, deleted=False)

    if not expenseclaim.rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/expenseclaim/pdf.html", request, {'object': expenseclaim}, [f.file for f in expenseclaim.get_pdf_files()])


@login_required
def cashbook_pdf(request, pk):
    from accounting_tools.models import CashBook

    cashbook = get_object_or_404(CashBook, pk=pk, deleted=False)

    if not cashbook.rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/cashbook/pdf.html", request, {'object': cashbook}, [f.file for f in cashbook.get_pdf_files()])

@login_required
def cashbook_csv(request, pk):
    from accounting_tools.models import CashBook
    from accounting_tools.models import CashBookLine
    from accounting_core.models import TVA

    cashbook = get_object_or_404(CashBook, pk=pk, deleted=False)

    if not cashbook.rights_can('SHOW', request.user):
        raise Http404
    if not cashbook.status[0] == '3':
        raise Http404(u'cashbook_not_accountable')
    if not cashbook.total_incomes() == cashbook.total_outcomes():
        raise Http404(u'Cashbook pas a 0, merci de le mettre a 0')    
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="'+slugify(cashbook.name)+'.csv"'

    #L'écriture du csv permet l'import dans sage comme définit ici : https://onlinehelp.sageschweiz.ch/sage-start/fr-ch/content/technique/d%C3%A9finition%20de%20l%20interface.htm
    writer = UnicodeCSVWriter(response)
    writer.writerow([0,cashbook.pk,'','',cashbook.name, cashbook.total_incomes(), cashbook.total_incomes(), '', '', 0, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',u'CASHBOOK#'+unicode(cashbook.pk)])
    first = True
    line_count = 1
    firstline = CashBookLine()
    for line in cashbook.get_lines(): 
        if first: #
            firstline = line
            first = False
            continue
        line_count = line_count + cashbook_line_write(writer, cashbook, line, line_count, False)
    line_count = line_count + cashbook_line_write(writer, cashbook, firstline, line_count, True)
    return response

def cashbook_line_write(writer, cashbook, line, line_number, last_line):
    from accounting_tools.models import CashBook
    from accounting_tools.models import CashBookLine
    from accounting_core.models import TVA
    initial_line_number = line_number
    try: 
        tva = TVA.objects.get(value=line.tva)
    except TVA.DoesNotExist: 
        raise Exception(u'TVA '+str(line.tva)+u' Not found - Impossible d\'exporter des lignes avec TVA speciales')
    if line.is_output(): 
        type = u'Débit' 
    else: 
        type = u'Crédit'
        
    if tva.value == 0.0:
        tva_string = u'Non soumis à la TVA'
        is_tva = False
    else: 
         tva_string = u'Soumis à la TVA'
         is_tva = True
    
    row = [u'1','','','','','','','','','','','',line_number,cashbook.pk,line.account.account_number,u'CHF',line.label,line.value, tva.code, tva.value, '', tva_string , type ,'',line.date.strftime(u"%d.%m.%Y"),0,line.value,line.value,0,u'CASHBOOK#'+unicode(cashbook.pk)]
    line_number = line_number + 1
    
    if is_tva: #on génère la ligne correspondante de tva si besoin
        tva_row = [u'1','','','','','','','','','','','',line_number,cashbook.pk,tva.account.account_number,u'CHF',line.label+u' - TVA',line.value_ttc-line.value, tva.code , tva.value, line_number-1 ,u'Montant TVA', type,'',line.date.strftime(u"%d.%m.%Y"),0,line.value_ttc-line.value,line.value_ttc-line.value,0,u'CASHBOOK#'+unicode(cashbook.pk)]
        line_number = line_number + 1
    
    if last_line == True: #la dernière écriture doit être de type 2
        if is_tva:
            tva_row[0] = u'2'
        else:
            row[0]=u'2'
    
    writer.writerow(row)
    if is_tva: 
        writer.writerow(tva_row)
        
    return line_number - initial_line_number #number of line written

@login_required
def get_withdrawal_infos(request, pk):
    from accounting_tools.models import Withdrawal

    withdrawal = get_object_or_404(Withdrawal, pk=pk, deleted=False)

    if not withdrawal.rights_can('SHOW', request.user):
        raise Http404

    return HttpResponse(json.dumps({'user_pk': withdrawal.user.pk, 'costcenter_pk': withdrawal.costcenter.pk, 'date': str(withdrawal.withdrawn_date)}), content_type='application/json')


@login_required
def withdrawal_available_list(request):
    """Return the list of available withdrawals for a given unit and year"""
    from accounting_tools.models import Withdrawal
    from accounting_core.models import AccountingYear
    from units.models import Unit

    withdrawals = Withdrawal.objects.filter(deleted=False, status="3_used").order_by('-withdrawn_date')

    if request.GET.get('upk'):
        unit = get_object_or_404(Unit, pk=request.GET.get('upk'))
        withdrawals = withdrawals.filter(costcenter__unit=unit)

    if request.GET.get('ypk'):
        accounting_year = get_object_or_404(AccountingYear, pk=request.GET.get('ypk'))
        withdrawals = withdrawals.filter(accounting_year=accounting_year)

    withdrawals = filter(lambda withdrawal: withdrawal.rights_can('SHOW', request.user), list(withdrawals))

    retour = {'data': [{'pk': withdrawal.pk, 'name': withdrawal.__unicode__(), 'used': withdrawal.status == '3_used'} for withdrawal in withdrawals]}

    return HttpResponse(json.dumps(retour), content_type='application/json')
    
class UnicodeCSVWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f):
        self.stream = f

    def writerow(self, row):
        for s in row: 
            if not isinstance(s, unicode):
                unicode(s).encode("utf-8")
            self.stream.write(s)
            self.stream.write(u'; ')
        self.stream.write(u'\r\n')
        
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)  