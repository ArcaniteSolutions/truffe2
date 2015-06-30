# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from app.utils import generate_pdf


@login_required
def export_demands_yearly(request, ypk):
    from accounting_core.models import AccountingYear
    from accounting_tools.models import Subvention

    if not Subvention.static_rights_can('EXPORT', request.user):
        raise Http404

    try:
        ay = AccountingYear.objects.get(pk=ypk)
        subv = [(ay.name, Subvention.objects.filter(accounting_year=ay).order_by('unit__name'))]
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
