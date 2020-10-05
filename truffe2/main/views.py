# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import InvalidPage, Paginator
from django.utils.timezone import now
from django.db import connection
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _


from haystack.views import SearchView
from sendfile import sendfile


def _home_news(request):

    from main.models import HomePageNews

    news = HomePageNews.objects.filter(status='1_online', deleted=False).order_by('-pk').all()

    news = filter(lambda s: (not s.start_date or s.start_date <= now()) and (not s.end_date or s.end_date >= now()), list(news))

    return {'news': news}


def _home_accreds(request):

    from units.models import Accreditation

    return {'accreds_to_validate': Accreditation.objects.filter(end_date=None, need_validation=True)}


def _home_invoices(request):

    from accounting_tools.models import Invoice

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.rights_in_root_unit(request.user, 'TRESORERIE') or request.user.is_superuser:
        invoices_need_bvr = Invoice.objects.filter(deleted=False, status='1_need_bvr').order_by('-pk')
        invoices_attente_accord = Invoice.objects.filter(deleted=False, status='2_ask_accord').order_by('-pk')
	invoices_waiting = Invoice.objects.filter(deleted=False, status='3_sent').order_by('-pk')
    else:
        invoices_need_bvr = None
        invoices_attente_accord = None
        invoices_waiting = filter(lambda i: i.rights_can('SHOW', request.user), Invoice.objects.filter(deleted=False, status='3_sent'))

    return {'invoices_need_bvr': invoices_need_bvr, 'invoices_attente_accord': invoices_attente_accord, 'invoices_waiting': invoices_waiting}


def _home_internal_transferts(request):

    from accounting_tools.models import InternalTransfer

    internaltransfer_to_validate, internaltransfer_to_account = None, None

    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
        internaltransfer_to_validate = InternalTransfer.objects.filter(deleted=False, status='1_agep_validable').order_by('-pk')

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        internaltransfer_to_account = InternalTransfer.objects.filter(deleted=False, status='2_accountable').order_by('-pk')

    return {'internaltransfer_to_validate': internaltransfer_to_validate, 'internaltransfer_to_account': internaltransfer_to_account}


def _home_withdrawals(request):

    from accounting_tools.models import Withdrawal

    rcash_to_validate = Withdrawal.objects.filter(deleted=False, status='1_agep_validable').order_by('-desired_date')
    rcash_to_withdraw = Withdrawal.objects.filter(deleted=False, status='2_withdrawn').order_by('-withdrawn_date')
    rcash_to_justify = Withdrawal.objects.filter(deleted=False, status='3_used').order_by('-withdrawn_date')

    if not request.user.rights_in_root_unit(request.user, 'SECRETARIAT') and not request.user.is_superuser:
        rcash_to_withdraw = filter(lambda rcash: rcash.rights_can_SHOW(request.user), list(rcash_to_withdraw))
        rcash_to_justify = filter(lambda rcash: rcash.rights_can_SHOW(request.user), list(rcash_to_justify))
        rcash_to_validate = None

    return {'rcash_to_validate': rcash_to_validate, 'rcash_to_withdraw': rcash_to_withdraw, 'rcash_to_justify': rcash_to_justify}


def _home_accounting_lines(request):

    from units.models import Unit
    from accounting_main.models import AccountingLine

    lines_status_by_unit = {}

    # ça serait beaucoup trop lourd de tester toutes les lignes, on fait donc
    # de manière fausse: basée sur les droits
    for unit in Unit.objects.filter(deleted=False).order_by('name'):
        if request.user.rights_in_unit(request.user, unit, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
            lines_status_by_unit[unit] = (AccountingLine.objects.filter(deleted=False, costcenter__unit=unit, status='0_imported').exclude(accounting_year__status='3_archived').count(), 
                                          AccountingLine.objects.filter(deleted=False, costcenter__unit=unit, status='2_error').exclude(accounting_year__status='3_archived').count())

    return {'lines_status_by_unit': lines_status_by_unit}


def _home_accounting_errors(request):

    from accounting_main.models import AccountingError

    open_errors = []

    for error in AccountingError.objects.filter(deleted=False).exclude(status='2_fixed').exclude(accounting_year__status='3_archived').order_by('pk'):
        if error.rights_can('SHOW', request.user):
            open_errors.append(error)

    return {'open_errors': open_errors}


def _home_expenseclaim(request):

    from accounting_tools.models import ExpenseClaim

    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
        expenseclaim_to_validate = ExpenseClaim.objects.filter(deleted=False, status__in=['1_unit_validable', '2_agep_validable', '3_agep_sig1', '3_agep_sig2']).order_by('status', '-pk')
    else:
        expenseclaim_to_validate = sorted(filter(lambda ec: ec.is_unit_validator(request.user), list(ExpenseClaim.objects.filter(deleted=False, status='1_unit_validable'))), key=lambda ec: -ec.pk)

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        expenseclaim_to_account = ExpenseClaim.objects.filter(deleted=False, status__in=['4_accountable', '5_in_accounting']).order_by('status', 'pk')
    else:
        expenseclaim_to_account = None

    return {'expenseclaim_to_validate': expenseclaim_to_validate, 'expenseclaim_to_account': expenseclaim_to_account}


def _home_cashbook(request):

    from accounting_tools.models import CashBook

    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
        cashbook_to_validate = CashBook.objects.filter(deleted=False, status__in=['1_unit_validable', '2_agep_validable', '3_agep_sig1', '3_agep_sig2']).order_by('status', '-pk')
    else:
        cashbook_to_validate = sorted(filter(lambda cb: cb.is_unit_validator(request.user), list(CashBook.objects.filter(deleted=False, status='1_unit_validable'))), key=lambda cb: -cb.pk)

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        cashbook_to_account = CashBook.objects.filter(deleted=False, status__in=['4_accountable', '5_in_accounting']).order_by('status', 'pk')
    else:
        cashbook_to_account = None

    return {'cashbook_to_validate': cashbook_to_validate, 'cashbook_to_account': cashbook_to_account}


def _home_providerInvoice(request):

    from accounting_tools.models import ProviderInvoice

    if request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser:
        providerinvoice_to_validate = ProviderInvoice.objects.filter(deleted=False, status__in=['1_unit_validable', '2_agep_validable']).order_by('-pk')
    else:
        providerinvoice_to_validate = sorted(filter(lambda ec: ec.is_unit_validator(request.user), list(ProviderInvoice.objects.filter(deleted=False, status='1_unit_validable'))), key=lambda ec: -ec.pk)

    if request.user.rights_in_root_unit(request.user, 'SECRETARIAT') or request.user.is_superuser:
        providerinvoice_to_account = ProviderInvoice.objects.filter(deleted=False, status='3_accountable').order_by('pk')
    else:
        providerinvoice_to_account = None

    return {'providerinvoice_to_validate': providerinvoice_to_validate, 'providerinvoice_to_account': providerinvoice_to_account}


@login_required
def home(request):
    """Home page dashboard"""

    from units.models import Accreditation

    BOXES = [
        # (lambda request: should_show, Function to call, template)
        (lambda request: True, _home_news, "news.html"),
        (lambda request: True, lambda request: {}, "moderate.html"),
        (lambda request: Accreditation.static_rights_can('VALIDATE', request.user), _home_accreds, "accreds_to_validate.html"),
        (lambda request: request.user.rights_in_any_unit('TRESORERIE') or request.user.is_superuser, _home_invoices, "invoices.html"),
        (lambda request: request.user.rights_in_root_unit(request.user, ['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser, _home_internal_transferts, "internaltransfers.html"),
        (lambda request: request.user.rights_in_any_unit(['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser, _home_withdrawals, "withdrawals.html"),
        (lambda request: request.user.rights_in_any_unit(['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser, _home_expenseclaim, "expenseclaims.html"),
        (lambda request: request.user.rights_in_any_unit(['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser, _home_cashbook, "cashbooks.html"),
        (lambda request: request.user.rights_in_any_unit('TRESORERIE') or request.user.is_superuser, _home_accounting_lines, "accounting_lines.html"),
        (lambda request: request.user.rights_in_any_unit('TRESORERIE') or request.user.is_superuser, _home_accounting_errors, "accounting_errors.html"),
        (lambda request: request.user.rights_in_any_unit(['TRESORERIE', 'SECRETARIAT']) or request.user.is_superuser, _home_providerInvoice, "providerInvoice.html"),
    ]

    data = {}

    boxes_to_show = []

    for (should_show, get_data, template) in BOXES:
        if should_show(request):
            data.update(get_data(request))
            boxes_to_show.append('main/box/{}'.format(template))

    ordered_boxes_to_show = []

    user_order = ['main/box/{}'.format(x) for x in request.user.homepage.split(',')] if request.user.homepage else []

    for box in user_order:
        if box in boxes_to_show:
            ordered_boxes_to_show.append(box)

    for box in boxes_to_show:
        if box not in user_order:
            ordered_boxes_to_show.append(box)

    data.update({'boxes_to_show': ordered_boxes_to_show})

    from main.models import SignableDocument

    for document in SignableDocument.objects.filter(deleted=False, active=True):
        if document.should_sign(request.user) and not document.signed(request.user):
            return redirect(reverse('main.views.signabledocument_sign', args=(document.pk,)))

    return render(request, 'main/home.html', data)


@login_required
def get_to_moderate(request):

    from generic.models import moderable_things

    liste = {}

    for model_class in moderable_things:

        moderable = model_class.objects.order_by('-pk').filter(status='1_asking').exclude(deleted=True)
        moderable = filter(lambda x: x.rights_can('VALIDATE', request.user), moderable)

        if moderable:
            liste[model_class] = moderable

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


class HaystackSearchView(SearchView):
    """Custom search view for haystack search"""

    template = 'main/search.html'

    def get_results(self):
        results = super(HaystackSearchView, self).get_results().order_by('-last_edit_date')
        return results

    def build_page(self):
        try:
            page_no = int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            page_no = 1

        if page_no < 1:
            page_no = 1

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
            page = paginator.page(1)

        return (paginator, page)

    def extra_context(self):
        return {'simple_search': not self.request.user.rights_can('FULL_SEARCH', self.request.user)}


@login_required
def set_homepage(request):

    request.user.homepage = request.GET.get('data', '')
    request.user.save()

    return HttpResponse('')


@login_required
def file_download(request, pk):

    from main.models import File
    file = get_object_or_404(File, pk=pk, deleted=False)

    if not file.rights_can('DOWNLOAD', request.user):
        raise Http404

    return sendfile(request, file.file.path, True)


@login_required
def file_download_list(request):

    from main.models import File

    group = request.GET.get('group')

    if group not in ('accounting', 'cs', 'misc'):
        raise Http404

    if not File.static_rights_can('LIST_{}'.format(group.upper()), request.user):
        raise Http404

    files = File.objects.filter(deleted=False, group=group).order_by('title')

    if request.user.is_external():
        files = files.filter(access='all')

    return render(request, 'main/file/download.html', {'files': files, 'group': group})


@login_required
def signabledocument_download(request, pk):

    from main.models import SignableDocument
    file = get_object_or_404(SignableDocument, pk=pk, deleted=False)

    if not file.rights_can('SHOW', request.user):

        if not file.should_sign(request.user):
            if not file.signed(request.user):
                raise Http404

    return sendfile(request, file.file.path, True)


@login_required
def signabledocument_sign(request, pk):

    from main.models import SignableDocument, Signature
    file = get_object_or_404(SignableDocument, pk=pk, deleted=False)

    if not file.should_sign(request.user) and not file.signed(request.user):
        raise Http404

    signed = file.signed(request.user)

    if request.method == 'POST' and not signed:

        Signature(
            user=request.user,
            document=file,
            ip=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '?')).split(',')[0],
            useragent=request.META.get('HTTP_USER_AGENT', '?'),
            document_sha=file.sha
        ).save()

        messages.success(request, _(u'Document signé !'))
        return redirect('main.views.signabledocument_signs')

    return render(request, 'main/signabledocument/sign.html', {'file': file, 'signed': signed})


@login_required
def signabledocument_signs(request):

    from main.models import SignableDocument

    signatures = request.user.signature_set.order_by('-when')

    documents = filter(lambda d: d.should_sign(request.user), SignableDocument.objects.filter(deleted=False, active=True))

    for d in documents:
        d.user_signed = d.signed(request.user)

    return render(request, 'main/signabledocument/signs.html', {'signatures': signatures, 'documents': documents})
