# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

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
        subventions = Subvention.objects.filter(accounting_year=ay).order_by('unit__name')
        if subventions:
            subventions = list(subventions) + [get_statistics(subventions)]
        subv = [(ay.name, subventions)]
    except AccountingYear.DoesNotExist:
        subv = [(_(u'Période inconnue'), Subvention.objects.none())]

    return generate_pdf("accounting_tools/subvention/subventions_pdf.html", {'subventions': subv, 'user': request.user, 'cdate': now()})


@login_required
def export_all_demands(request):
    from accounting_core.models import AccountingYear
    from accounting_tools.models import Subvention

    if not Subvention.static_rights_can('EXPORT', request.user):
        raise Http404

    years = AccountingYear.objects.order_by('start_date')
    subventions = []
    for ay in years:
        subv = Subvention.objects.filter(accounting_year=ay).order_by('unit__name')
        if subv:
            subv = list(subv) + [get_statistics(subv)]
        subventions.append((ay.name, subv))

    summary = []
    units = map(lambda subv: subv.get_real_unit_name(), sorted(list(Subvention.objects.distinct('unit', 'unit_blank_name')), key=lambda subv: subv.get_real_unit_name()))
    for unit_name in units:
        line = [unit_name]
        for year in years:
            year_subv = Subvention.objects.filter(accounting_year=year).filter(Q(unit__name=unit_name) | Q(unit_blank_name=unit_name)).first()
            if year_subv:
                line += [year_subv.amount_asked, year_subv.amount_given, year_subv.mobility_asked, year_subv.mobility_asked]
            else:
                line += ["", "", "", ""]
        summary.append(line)

    return generate_pdf("accounting_tools/subvention/subventions_pdf.html", {'subventions': subventions, 'summary': summary, 'years': years, 'user': request.user, 'cdate': now()})
