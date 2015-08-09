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


@login_required
def home(request):
    """Dummy home page"""

    from main.models import HomePageNews
    from accounting_tools.models import InternalTransfer, Withdrawal, ExpenseClaim, Invoice

    news = HomePageNews.objects.filter(status='1_online').order_by('-pk').all()

    news = filter(lambda s: (not s.start_date or s.start_date <= now()) and (not s.end_date or s.end_date >= now()), list(news))

    from units.models import Accreditation, Unit

    if Accreditation.static_rights_can('VALIDATE', request.user):
        accreds_to_validate = Accreditation.objects.filter(end_date=None, need_validation=True)
    else:
        accreds_to_validate = []

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        invoices_need_bvr = Invoice.objects.filter(deleted=False, status='1_need_bvr').order_by('-pk')
        invoices_waiting = Invoice.objects.filter(deleted=False, status='2_sent').order_by('-pk')
    else:
        invoices_need_bvr = None
        invoices_waiting = filter(lambda i: i.rights_can('SHOW', request.user), Invoice.objects.filter(deleted=False, status='2_sent'))

    internaltransfer_to_validate, internaltransfer_to_account = None, None
    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
        internaltransfer_to_validate = InternalTransfer.objects.filter(deleted=False, status='1_agep_validable').order_by('-pk')
    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        internaltransfer_to_account = InternalTransfer.objects.filter(deleted=False, status='2_accountable').order_by('-pk')

    rcash_to_validate = Withdrawal.objects.filter(deleted=False, status='1_agep_validable').order_by('-desired_date')
    rcash_to_withdraw = Withdrawal.objects.filter(deleted=False, status='2_withdrawn').order_by('-withdrawn_date')
    rcash_to_justify = Withdrawal.objects.filter(deleted=False, status='3_used').order_by('-withdrawn_date')

    if not request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or not request.user.is_superuser:
        rcash_to_withdraw = filter(lambda rcash: rcash.rights_can_SHOW(request.user), list(rcash_to_withdraw))
        rcash_to_justify = filter(lambda rcash: rcash.rights_can_SHOW(request.user), list(rcash_to_justify))
        rcash_to_validate = None

    from accounting_main.models import AccountingLine, AccountingError

    lines_status_by_unit = {}

    # ça serait beaucoup trop lourd de tester toutes les lignes, on fait donc
    # de manière fausse: basée sur les droits
    for unit in Unit.objects.filter(deleted=False).order_by('name'):
        if request.user.rights_in_unit(request.user, unit, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
            lines_status_by_unit[unit] = (AccountingLine.objects.filter(deleted=False, costcenter__unit=unit, status='0_imported').count(), AccountingLine.objects.filter(deleted=False, costcenter__unit=unit, status='2_error').count())

    open_errors = []

    for error in AccountingError.objects.filter(deleted=False).exclude(status='2_fixed').order_by('pk'):
        if error.rights_can('SHOW', request.user):
            open_errors.append(error)

    expenseclaim_to_account = None
    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
        expenseclaim_to_validate = ExpenseClaim.objects.filter(deleted=False, status__in=['1_unit_validable', '2_agep_validable']).order_by('-pk')
    else:
        expenseclaim_to_validate = sorted(filter(lambda ec: ec.is_unit_validator(request.user), list(ExpenseClaim.objects.filter(deleted=False, status='1_unit_validable'))), key=lambda ec: -ec.pk)

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        expenseclaim_to_account = ExpenseClaim.objects.filter(deleted=False, status='3_accountable').order_by('pk')

    return render(request, 'main/home.html', {'news': news, 'accreds_to_validate': accreds_to_validate, 'internaltransfer_to_validate': internaltransfer_to_validate,
                                              'internaltransfer_to_account': internaltransfer_to_account, 'rcash_to_validate': rcash_to_validate, 'rcash_to_withdraw': rcash_to_withdraw,
                                              'rcash_to_justify': rcash_to_justify, 'invoices_need_bvr': invoices_need_bvr, 'invoices_waiting': invoices_waiting,
                                              'lines_status_by_unit': lines_status_by_unit, 'open_errors': open_errors,
                                              'expenseclaim_to_validate': expenseclaim_to_validate, 'expenseclaim_to_account': expenseclaim_to_account})


@login_required
def get_to_moderate(request):

    from generic.models import moderable_things

    liste = {}

    for model_class in moderable_things:

        moderable = model_class.objects.order_by('-pk').filter(status='1_asking').exclude(deleted=True)
        moderable = filter(lambda x: x.rights_can('VALIDATE', request.user), moderable)

        if moderable:
            liste[model_class.MetaData.base_title] = moderable

    return render(request, 'main/to_moderate.html', {'liste': liste})
