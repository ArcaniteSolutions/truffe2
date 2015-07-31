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
import json
import time
import collections


from app.utils import update_current_unit, update_current_year
from generic.views import get_unit_data, get_year_data
from notifications.utils import notify_people


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
def copy_budget(request, pk):
    from accounting_main.models import Budget

    budgets = [get_object_or_404(Budget, pk=pk_, deleted=False) for pk_ in filter(lambda x: x, pk.split(','))]

    for bud in budgets:
        if not bud.rights_can('EDIT', request.user):
            raise Http404

        old_lines = bud.budgetline_set.all()
        bud.name = 'Copy of {}'.format(bud.name)
        bud.id = None
        bud.save()

        for line in old_lines:
            line.budget = bud
            line.id = None
            line.save()

    messages.success(request, _(u'Copie terminée avec succès'))

    if len(budgets) == 1:
        return redirect('accounting_main.views.budget_edit', budgets[0].pk)
    else:
        return redirect('accounting_main.views.budget_list')

@login_required
def budget_getinfos(request, pk):
    from accounting_main.models import Budget

    budget = get_object_or_404(Budget, pk=pk)
    if not budget.rights_can_EDIT(request.user):
        raise Http404

    lines = map(lambda line: {'table_id': 'incomes' if line.amount > 0 else 'outcomes', 'account_id': line.account.pk,
                              'description': line.description, 'amount': abs(float(line.amount))}, list(budget.budgetline_set.all()))
    accounts = set(map(lambda line: line['account_id'], lines))
    retour = [[line for line in lines if line['account_id'] == acc] for acc in accounts]

    return HttpResponse(json.dumps(retour), content_type='application/json')
