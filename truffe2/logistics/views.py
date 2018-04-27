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

import json

from app.utils import generate_pdf
from app.utils import update_current_unit
from generic.templatetags.generic_extras import html_check_and_safe


@login_required
def room_search(request):

    from logistics.models import Room, RoomReservation

    q = request.GET.get('q')
    init = request.GET.get('init')
    unit_pk = request.GET.get('unit_pk', "-1") or "-1"

    rooms = Room.objects.filter(active=True, deleted=False).order_by('title')

    if q:
        rooms = rooms.filter(title__icontains=q)

    if init is not None:
        if not init:
            return HttpResponse(json.dumps([]))
        rooms = rooms.filter(pk=init)

    if unit_pk == "-1":
        rooms = rooms.filter(allow_externals=True)
    else:
        # Pas de filtre, mais on check que le dude peut faire une réservation
        # dans l'unité
        from units.models import Unit
        get_object_or_404(Unit, pk=unit_pk)

        dummy = RoomReservation()
        update_current_unit(request, unit_pk)

        if not dummy.rights_can('CREATE', request.user):
            raise Http404

    retour = map(lambda room: {'id': room.pk, 'text': room.title, 'description': strip_tags(html_check_and_safe(room.description))[:100] + '...', 'unit': str(room.unit)}, rooms)

    return HttpResponse(json.dumps(retour))


@login_required
def supply_search(request):

    from logistics.models import Supply, SupplyReservation

    q = request.GET.get('q')
    init = request.GET.get('init')
    unit_pk = request.GET.get('unit_pk', "-1") or "-1"

    supplies = Supply.objects.filter(active=True, deleted=False).order_by('title')

    if q:
        supplies = supplies.filter(title__icontains=q)

    if init is not None:
        if not init:
            return HttpResponse(json.dumps([]))
        supplies = supplies.filter(pk=init)

    if unit_pk == "-1":
        supplies = supplies.filter(allow_externals=True)
    else:
        # Pas de filtre, mais on check que le dude peut faire une réservation
        # dans l'unité
        from units.models import Unit
        get_object_or_404(Unit, pk=unit_pk)

        dummy = SupplyReservation()
        update_current_unit(request, unit_pk)

        if not dummy.rights_can('CREATE', request.user):
            raise Http404

    retour = map(lambda supply: {'id': supply.pk, 'text': supply.title, 'description': strip_tags(html_check_and_safe(supply.description))[:100] + '...', 'unit': str(supply.unit)}, supplies)

    return HttpResponse(json.dumps(retour))

@login_required
def loanagreement_pdf(request, pk):

    from logistics.models import SupplyReservation

    reservation = get_object_or_404(SupplyReservation, pk=pk, deleted=False)

    if not reservation.rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("logistics/supplyreservation/pdf.html", request, {'supplyreservation': reservation})
