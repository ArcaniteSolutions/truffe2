# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.conf import settings


import os
from PIL import Image


from app.utils import generate_pdf


def get_statistics(subventions):
    """Given a set of subventions, return statistics about comms and assocs."""
    assoc = subventions.filter(unit=None).aggregate(Sum('amount_asked'), Sum('amount_given'), Sum('mobility_asked'), Sum('mobility_given'))
    comms = subventions.exclude(unit=None).aggregate(Sum('amount_asked'), Sum('amount_given'), Sum('mobility_asked'), Sum('mobility_given'))

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
        subventions = Subvention.objects.filter(accounting_year=ay).order_by('unit__name', 'unit_blank_name')
        if subventions:
            subventions = list(subventions) + [get_statistics(subventions)]
        subv = [(ay.name, subventions)]
    except AccountingYear.DoesNotExist:
        subv = [(_(u'Période inconnue'), Subvention.objects.none())]

    return generate_pdf("accounting_tools/subvention/subventions_pdf.html", {'subventions': subv, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})


@login_required
def export_all_demands(request):
    from accounting_core.models import AccountingYear
    from accounting_tools.models import Subvention

    if not Subvention.static_rights_can('EXPORT', request.user):
        raise Http404

    years = AccountingYear.objects.order_by('start_date')
    subventions = []
    for ay in years:
        subv = Subvention.objects.filter(accounting_year=ay).order_by('unit__name', 'unit_blank_name')
        if subv:
            subv = list(subv) + [get_statistics(subv)]
        subventions.append((ay.name, subv))

    summary = []
    units = sorted(list(set(map(lambda subv: subv.get_real_unit_name(), list(Subvention.objects.all())))))
    for unit_name in units:
        line = [unit_name]
        for year in years:
            year_subv = Subvention.objects.filter(accounting_year=year).filter(Q(unit__name=unit_name) | Q(unit_blank_name=unit_name)).first()
            if year_subv:
                line += [year_subv.amount_asked, year_subv.amount_given, year_subv.mobility_asked, year_subv.mobility_asked]
            else:
                line += ["", "", "", ""]
        summary.append(line)

    return generate_pdf("accounting_tools/subvention/subventions_pdf.html", {'subventions': subventions, 'summary': summary, 'years': years, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})


@login_required
def invoice_pdf(request, pk):

    from accounting_tools.models import Invoice

    invoice = get_object_or_404(Invoice, pk=pk, deleted=False)

    if not invoice.static_rights_can('SHOW', request.user):
        raise Http404

    img = invoice.generate_bvr()
    img = img.resize((1414, 1000), Image.LANCZOS)
    img.save(os.path.join(settings.MEDIA_ROOT, 'cache/bvr/{}.png').format(invoice.pk))

    return generate_pdf("accounting_tools/invoice/pdf.html", {'invoice': invoice, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})


@login_required
def invoice_bvr(request, pk):

    from accounting_tools.models import Invoice

    invoice = get_object_or_404(Invoice, pk=pk, deleted=False)

    if not invoice.static_rights_can('SHOW', request.user):
        raise Http404

    img = invoice.generate_bvr()

    response = HttpResponse(mimetype="image/png")
    img.save(response, 'png')
    return response


@login_required
def withdrawal_pdf(request, pk):

    from accounting_tools.models import Withdrawal

    withdrawal = get_object_or_404(Withdrawal, pk=pk, deleted=False)

    if not withdrawal.static_rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/withdrawal/pdf.html", {'object': withdrawal, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})


@login_required
def internaltransfer_pdf(request, pk):
    from accounting_tools.models import InternalTransfer

    internaltransfer = get_object_or_404(InternalTransfer, pk=pk, deleted=False)

    if not internaltransfer.static_rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/internaltransfer/pdf.html", {'object': internaltransfer, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})


@login_required
def expenseclaim_pdf(request, pk):
    from accounting_tools.models import ExpenseClaim

    expenseclaim = get_object_or_404(ExpenseClaim, pk=pk, deleted=False)

    if not expenseclaim.static_rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/expenseclaim/pdf.html", {'object': expenseclaim, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})


@login_required
def cashbook_pdf(request, pk):
    from accounting_tools.models import CashBook

    cashbook = get_object_or_404(CashBook, pk=pk, deleted=False)

    if not cashbook.static_rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("accounting_tools/cashbook/pdf.html", {'object': cashbook, 'user': request.user, 'cdate': now(), 'MEDIA_ROOT': settings.MEDIA_ROOT})
