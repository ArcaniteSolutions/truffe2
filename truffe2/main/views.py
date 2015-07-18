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
    from accounting_tools.models import InternalTransfer, Withdrawal

    news = HomePageNews.objects.filter(status='1_online').order_by('-pk').all()

    news = filter(lambda s: (not s.start_date or s.start_date <= now()) and (not s.end_date or s.end_date >= now()), list(news))

    from units.models import Accreditation

    if Accreditation.static_rights_can('VALIDATE', request.user):
        accreds_to_validate = Accreditation.objects.filter(end_date=None, need_validation=True)
    else:
        accreds_to_validate = []

    internaltransfer_to_validate = None
    internaltransfer_to_account = None
    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']):
        internaltransfer_to_validate = InternalTransfer.objects.filter(deleted=False, status='1_agep_validable')
    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT'):
        internaltransfer_to_account = InternalTransfer.objects.filter(deleted=False, status='2_accountable')

    rcash_to_validate = Withdrawal.objects.filter(deleted=False, status='1_agep_validable').order_by('desired_date')
    rcash_to_withdraw = Withdrawal.objects.filter(deleted=False, status='2_withdrawn').order_by('withdrawn_date')
    rcash_to_justify = Withdrawal.objects.filter(deleted=False, status='3_used').order_by('withdrawn_date')
    if not request.user.rights_in_root_unit(request.user, 'SECRETARIAT'):
        for rcash_qs in [rcash_to_withdraw, rcash_to_justify]:
            rcash_qs = filter(lambda rcash: rcash.rights_can_SHOW(request.user), list(rcash_qs))
        rcash_to_validate = None

    return render(request, 'main/home.html', {'news': news, 'accreds_to_validate': accreds_to_validate, 'internaltransfer_to_validate': internaltransfer_to_validate,
                                              'internaltransfer_to_account': internaltransfer_to_account, 'rcash_to_validate': rcash_to_validate, 'rcash_to_withdraw': rcash_to_withdraw,
                                              'rcash_to_justify': rcash_to_justify})


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
