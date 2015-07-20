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
import datetime
import time


def accounting_graph(request):

    from accounting_core.models import CostCenter
    from accounting_main.models import AccountingLine

    costcenter = get_object_or_404(CostCenter, pk=request.GET.get('costcenter'))

    if not AccountingLine.static_rights_can('LIST', request.user, costcenter.unit, costcenter.accounting_year):
        raise Http404

    data = {}

    for line in AccountingLine.objects.filter(costcenter=costcenter).order_by('date'):
        timestamp = int((time.mktime(line.date.timetuple()) + 3600) * 1000)
        data[timestamp] = line.current_sum

    return render(request, 'accounting_main/accountingline/graph.html', {'costcenter': costcenter, 'random': str(uuid.uuid4()), 'data': data})


def errors_send_message(request, pk):
    from accounting_main.models import AccountingError, AccountingErrorMessage

    error = get_object_or_404(AccountingError, pk=pk)

    if not error.rights_can('ADD_COMMENT', request.user):
        raise Http404

    AccountingErrorMessage(author=request.user, message=request.POST.get('message'), error=error).save()

    messages.success(request, _(u'Message ajouté !'))

    return HttpResponse('')
