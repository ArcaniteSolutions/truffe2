# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q


import json


from accounting_core import models as accounting_models
from app.utils import update_current_year, generate_pdf
from generic.models import copiable_things


@login_required
def copy_accounting_year(request, pk):
    from accounting_core.models import AccountingYear

    accounting_years = [get_object_or_404(AccountingYear, pk=pk_) for pk_ in filter(lambda x: x, pk.split(','))]

    for ay in accounting_years:
        if not ay.rights_can('EDIT', request.user):
            raise Http404

        copiable_objects = {}
        for copiable_class in copiable_things:
            copiable_objects[copiable_class] = getattr(ay, '{}_set'.format(copiable_class.__name__.lower())).all()

        ay.name = 'Copy of {}'.format(ay.name)
        ay.id = None
        ay.save()

        for cp_obj in copiable_objects.values():
            # Create the new objects
            for elem in cp_obj:
                elem.accounting_year = ay
                elem.id = None
                elem.save()

        for cp_class, cp_obj in copiable_objects.iteritems():
            # Correct dependencies on the new objects
            if hasattr(cp_class.MetaAccounting, 'foreign'):
                for (field_name, field_class) in cp_class.MetaAccounting.foreign:
                    for elem in cp_obj:
                        if getattr(elem, field_name):  # if it was None, remains None
                            setattr(elem, field_name, getattr(accounting_models, field_class).objects.get(accounting_year=ay, name=getattr(elem, field_name).name))
                        elem.save()

    messages.success(request, _(u'Copie terminée avec succès'))

    if len(accounting_years) == 1:
        update_current_year(request, accounting_years[0].pk)
        return redirect('accounting_core.views.accountingyear_edit', accounting_years[0].pk)
    else:
        return redirect('accounting_core.views.accountingyear_list')


@login_required
def costcenter_available_list(request):
    """Return the list of available costcenters for a given unit and year"""
    from units.models import Unit
    from accounting_core.models import AccountingYear, CostCenter

    costcenters = CostCenter.objects.filter(deleted=False).order_by('account_number')

    if request.GET.get('upk'):
        unit = get_object_or_404(Unit, pk=request.GET.get('upk'))
        costcenters = costcenters.filter(unit=unit)

    if request.GET.get('ypk'):
        accounting_year = get_object_or_404(AccountingYear, pk=request.GET.get('ypk'))
        costcenters = costcenters.filter(accounting_year=accounting_year)

    retour = {'data': [{'pk': costcenter.pk, 'name': costcenter.__unicode__()} for costcenter in costcenters]}

    return HttpResponse(json.dumps(retour), content_type='application/json')


@login_required
def pdf_list_cost_centers(request, pk):
    from accounting_core.models import AccountingYear, CostCenter

    try:
        ay = AccountingYear.objects.get(pk=pk)
    except AccountingYear.DoesNotExist:
        raise Http404

    if not ay.rights_can('EDIT', request.user):
        raise Http404

    cc = CostCenter.objects.filter(accounting_year=ay).order_by('account_number')

    return generate_pdf("accounting_core/costcenter/liste_pdf.html", {'cost_centers': cc, 'ay': ay, 'user': request.user, 'cdate': now()})


@login_required
def pdf_list_accounts(request, pk):
    from accounting_core.models import AccountingYear, AccountCategory

    try:
        ay = AccountingYear.objects.get(pk=pk)
    except AccountingYear.DoesNotExist:
        raise Http404

    if not ay.rights_can('EDIT', request.user):
        raise Http404

    root_ac = AccountCategory.objects.filter(accounting_year=ay, parent_hierarchique=None).order_by('order')

    return generate_pdf("accounting_core/account/liste_pdf.html", {'root_ac': root_ac, 'ay': ay, 'user': request.user, 'cdate': now()})


@login_required
def tva_available_list(request):
    """Return the list of available TVA for a user"""
    from accounting_core.models import TVA

    tvas = TVA.objects.filter(deleted=False).order_by('value')

    if not TVA.static_rights_can('ANYTVA', request.user):
        tvas = tvas.filter(onlyagepoly=False)

    q = request.GET.get('q')
    init = request.GET.get('init')

    bonus_tva = []

    if q:
        try:
            value_q = float(q)
            tvas = tvas.filter(Q(name__istartswith=q) | Q(value__istartswith=value_q))

            if TVA.static_rights_can('ANYTVA', request.user):
                bonus_tva = [{'id': value_q, 'text': '{}% (TVA Spéciale)'.format(value_q)}]
        except:
            tvas = tvas.filter(name__istartswith=q)

    if init:
        try:
            value_q = float(init)
            tvas = tvas.filter(Q(value__istartswith=value_q))

            bonus_tva = [{'id': value_q, 'text': '{}% (TVA Spéciale)'.format(value_q)}]
        except:
            tvas = tvas.filter(name__istartswith=q)

    retour = [{'id': float(tva.value), 'text': tva.__unicode__()} for tva in tvas]

    if bonus_tva:
        bonus_tva_exists = False

        for tva_data in retour:
            if tva_data['id'] == bonus_tva[0]['id']:
                bonus_tva_exists = True

        if not bonus_tva_exists:
            retour = bonus_tva + retour

    return HttpResponse(json.dumps(retour), content_type='application/json')
