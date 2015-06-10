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

    main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

    main_unit.set_rights_can_select(lambda unit: Accreditation.static_rights_can('LIST', request.user, unit))
    main_unit.set_rights_can_edit(lambda unit: Accreditation.static_rights_can('CREATE', request.user, unit))
    main_unit.check_if_can_use_hidden(request.user)

    if request.GET.get('upk'):
        update_current_unit(request, request.GET.get('upk'))

    can_edit = Accreditation.static_rights_can('CREATE', request.user, get_current_unit(request))

    return render(request, 'units/accreds/list.html', {'main_unit': main_unit, 'can_edit': can_edit})


@login_required
@csrf_exempt
def accreds_list_json(request):
    """Display the list of accreds, json call for the list"""

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    unit = get_current_unit(request)

    # Check unit access
    if not Accreditation.static_rights_can('LIST', request.user, unit):
        raise Http404

    # Filter by unit
    filter_ = lambda x: x.filter(unit=unit)

    # Si pas le droit de créer, filtrage des accreds invisibles
    if not Accreditation.static_rights_can('CREATE', request.user, get_current_unit(request)):
        filter__ = lambda x: x.filter(hidden_in_truffe=False)
    else:
        filter__ = lambda x: x

    # Filter old accreds, if needed
    if request.GET.get('h', '0') == '0':
        filter2 = lambda x: filter_(filter__(x)).filter(end_date=None)
    else:
        filter2 = lambda x: filter_(filter__(x))

    return generic_list_json(request, Accreditation, ['user', 'get_role_or_display_name', 'start_date', 'exp_date', 'no_epfl_sync', 'pk'], 'units/accreds/list_json.html', filter_fields=['user__first_name', 'user__last_name', 'role__name'], bonus_filter_function=filter2, not_sortable_colums=['get_role_or_display_name'])


@login_required
def accreds_renew(request, pk):
    """Renew an accreds"""

    accred = get_object_or_404(Accreditation, pk=pk)

    if not accred.rights_can('EDIT', request.user):
        raise Http404

    accred.validation_date = now()
    accred.save()

    messages.success(request, _(u'Accréditation renouvellée !'))

    return redirect('units.views.accreds_list')


@login_required
def accreds_delete(request, pk):
    """Delete an accred"""

    accred = get_object_or_404(Accreditation, pk=pk)

    if not accred.rights_can('DELETE', request.user):
        raise Http404

    cannot_last_prez = False

    if accred.role.pk == settings.PRESIDENT_ROLE_PK and not accred.rights_can('INGORE_PREZ', request.user) and accred.unit.accreditation_set.filter(role__pk=settings.PRESIDENT_ROLE_PK, end_date=None).count() <= 1:
        cannot_last_prez = True

    if not cannot_last_prez and request.method == 'POST':
        accred.end_date = now()
        accred.save()

        accred.user.clear_rights_cache()

        messages.success(request, _(u'Accréditation supprimée !'))

        return redirect('units.views.accreds_list')

    return render(request, 'units/accreds/delete.html', {'accred': accred, 'cannot_last_prez': cannot_last_prez})


@login_required
def accreds_add(request):

    update_current_unit(request, request.GET.get('upk'))
    unit = get_current_unit(request)

    if not Accreditation.static_rights_can('CREATE', request.user, unit):
        raise Http404

    from units.forms2 import AccreditationAddForm

    done = False

    if request.method == 'POST':  # If the form has been submitted...
        form = AccreditationAddForm(request.user, request.POST)

        if form.is_valid():  # If the form is valid
            accred = form.save(commit=False)

            accred.unit = unit

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

            accred.user.clear_rights_cache()

            messages.success(request, _(u'Accréditation sauvegardée !'))

            done = True

    else:
        form = AccreditationAddForm(request.user)

    return render(request, 'units/accreds/add.html', {'form': form, 'done': done, 'unit': unit})


@login_required
def accreds_search(request):

    results = search_sciper(request.GET.get('q'))

    retour = map(lambda (sciper, data): {'id': sciper, 'text': '%s - %s %s (%s)' %data}, results.iteritems())

    return HttpResponse(json.dumps(retour))
