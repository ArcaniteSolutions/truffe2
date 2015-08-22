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
from django.db import connection


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


@login_required
def link_base(request):

    from main.models import Link
    from generic.views import get_unit_data

    unit_mode, current_unit, unit_blank = get_unit_data(Link, request)

    from units.models import Unit

    main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

    main_unit.set_rights_can_select(lambda unit: Link.static_rights_can('SHOW_BASE', request.user, unit, None))
    main_unit.set_rights_can_edit(lambda unit: Link.static_rights_can('SHOW_BASE', request.user, unit, None))
    main_unit.check_if_can_use_hidden(request.user)

    if Link.static_rights_can('SHOW_BASE', request.user, current_unit, None):
        links = Link.objects.filter(deleted=False, unit=current_unit, leftmenu=None).order_by('title')
    else:
        links = []

    return render(request, 'main/link/base.html', {'unit_mode': unit_mode, 'main_unit': main_unit, 'links': links})


@login_required
def last_100_logging_entries(request):
    if not request.user.is_superuser:
        raise Http404

    cursor = connection.cursor()

    from generic.models import GENERICS_MODELS

    query = """
        SELECT * FROM (
            {}
        ) as _ ORDER BY `when` DESC limit 100""".format(
            ' UNION ALL '.join(
                ["""( SELECT *, '{}' as model_id from {} order by `when` desc limit 100)""".format(key, GENERICS_MODELS[key][1]._meta.db_table) for key in GENERICS_MODELS]
            )
        )
    cursor.execute(query)

    data = []

    for row in cursor.fetchall():
        log_pk, when, extra_data, who_pk, what, obj_pk, key = row
        data.append(GENERICS_MODELS[key][1].objects.get(pk=log_pk))

    return render(request, 'main/last_100_logging_entries.html', {'data': data})


from haystack.views import SearchView

class MySearchView(SearchView):
    """My custom search view."""

    template = 'search/search.html'

    def get_results(self):
        results = super(MySearchView, self).get_results().order_by('-last_edit_date')
        return results

    def build_page(self):
        try:
            page_no = int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            raise Http404("Not a valid number for page.")

        if page_no < 1:
            raise Http404("Pages should be 1 or greater.")

        start_offset = (page_no - 1) * self.results_per_page

        # If the user is admin or head of agepoly, he can see almost all result
        # (filterted in template). If not, we filter here results to avoid
        # strange pagination
        if not self.request.user.rights_can('FULL_SEARCH', self.request.user):
            new_results = []

            for result in self.results:
                if len(new_results) > min(start_offset + self.results_per_page, settings.HAYSTACK_MAX_SIMPLE_SEARCH_RESULTS):
                    break

                if result.object.rights_can('SHOW', self.request.user):
                    new_results.append(result)

            new_results = new_results[:settings.HAYSTACK_MAX_SIMPLE_SEARCH_RESULTS]

            self.results = new_results

        self.results[start_offset:start_offset + self.results_per_page]

        paginator = Paginator(self.results, self.results_per_page)

        try:
            page = paginator.page(page_no)
        except InvalidPage:
            raise Http404("No such page!")

        return (paginator, page)

    def extra_context(self):
        return {'simple_search': not self.request.user.rights_can('FULL_SEARCH', self.request.user)}
