# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response, redirect
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


from generic.datatables import generic_list_json

from units.models import Accreditation
from app.utils import update_current_unit, get_current_unit
from app.ldaputils import search_sciper, get_attrs_of_sciper
from users.models import TruffeUser

import json


@login_required
def accreds_list(request):
    """Display the list of accreds"""

    from units.models import Unit

    main_unit = Unit.objects.get(pk=1)

    return render_to_response('units/accreds/list.html', {'main_unit': main_unit}, context_instance=RequestContext(request))


@login_required
@csrf_exempt
def accreds_list_json(request):
    """Display the list of accreds, json call for the list"""

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    # Filter by unit
    filter_ = lambda x: x.filter(unite=get_current_unit(request))

    # Filter old accreds, if needed
    if request.GET.get('h', '0') == '0':
        filter2 = lambda x: filter_(x).filter(end_date=None)
    else:
        filter2 = filter_

    return generic_list_json(request, Accreditation, ['user', 'get_role_or_display_name', 'start_date', 'exp_date', 'no_epfl_sync', 'pk'], 'units/accreds/list_json.html', filter_fields=['user__first_name', 'user__last_name', 'role__name'], bonus_filter_function=filter2)


@login_required
def accreds_renew(request, pk):
    """Renew an accreds"""

    accred = get_object_or_404(Accreditation, pk=pk)

    accred.validation_date = now()
    accred.save()

    messages.success(request, _(u'Accréditation renouvellée !'))

    return redirect('units.views.accreds_list')


@login_required
def accreds_delete(request, pk):
    """Delete an accred"""

    accred = get_object_or_404(Accreditation, pk=pk)

    if request.method == 'POST':
        accred.end_date = now()
        accred.save()

        messages.success(request, _(u'Accréditation supprimée !'))

        return redirect('units.views.accreds_list')

    return render_to_response('units/accreds/delete.html', {'accred': accred}, context_instance=RequestContext(request))


@login_required
def accreds_add(request):

    update_current_unit(request, request.GET.get('upk'))
    unite = get_current_unit(request)

    from units.forms2 import AccreditationAddForm

    done = False

    if request.method == 'POST':  # If the form has been submitted...
        form = AccreditationAddForm(request.user, request.POST)

        if form.is_valid():  # If the form is valid
            accred = form.save(commit=False)

            accred.unite = unite

            # Try to find the user. If he dosen't exists, create it.
            try:
                user = TruffeUser.objects.get(username=form.cleaned_data['user'])
            except TruffeUser.DoesNotExist:
                user = TruffeUser()

                user.username = form.cleaned_data['user']

                user.last_name, user.first_name, user.email = get_attrs_of_sciper(user.username)

                user.is_active = True

                user.save()

            accred.user = user
            accred.save()

            messages.success(request, _(u'Accréditation sauvegardé !'))

            done = True

    else:
        form = AccreditationAddForm(request.user)

    return render_to_response('units/accreds/add.html', {'form': form, 'done': done, 'unite': unite}, context_instance=RequestContext(request))


@login_required
def accreds_search(request):

    results = search_sciper(request.GET.get('q'))

    retour = map(lambda (sciper, data): {'id': sciper, 'text': '%s - %s %s (%s)' %data}, results.iteritems())

    return HttpResponse(json.dumps(retour))
