# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, redirect, render
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

from notifications.models import Notification
from generic.datatables import generic_list_json


@login_required
def dropdown(request):
    """Display the downdown menu for notificatoins"""

    if request.GET.get('read'):
        notification = get_object_or_404(Notification, pk=request.GET.get('read'), user=request.user)
        notification.seen = True
        notification.seen_date = now()
        notification.save()

    if request.GET.get('allread'):
        Notification.objects.filter(user=request.user, seen=False).update(seen=True, seen_date=now())
        pass

    notifications = Notification.objects.filter(user=request.user, seen=False).order_by('-creation_date')

    return render(request, 'notifications/dropdown.html', {'notifications': notifications})


@login_required
def goto(request, pk):

    notification = get_object_or_404(Notification, pk=pk, user=request.user)

    notification.seen = True
    notification.seen_date = now()
    notification.save()

    return HttpResponseRedirect(request.GET.get('next'))


@login_required
def notifications_count(request):

    if request.user.pk:
        notifications = Notification.objects.filter(user=request.user, seen=False)
        return {'notifications_count': notifications.count()}
    else:
        return {'notifications_count': 0}


@login_required
def notification_center(request):
    """Base display for the notification center"""

    return render(request, 'notifications/center/index.html', {})


@login_required
def notification_keys(request):
    """Display left type menu"""

    keys = []

    for key in Notification.objects.filter(user=request.user).values('key').distinct():
        key['nb_unread'] = Notification.objects.filter(user=request.user, seen=False, key=key['key']).count()
        keys.append(key)

    sorted(keys, key=lambda x: x['key'])

    all_unread = Notification.objects.filter(user=request.user, seen=False).count()

    return render(request, 'notifications/center/keys.html', {'keys': keys, 'current_type': request.GET.get('current_type'), 'all_unread': all_unread})


@login_required
@csrf_exempt
def notification_json(request):
    """Json for notifications"""

    current_type = request.GET.get('current_type')

    if current_type:
        bonus_filter = lambda x: x.filter(key=current_type, user=request.user)
    else:
        bonus_filter = lambda x: x.filter(user=request.user)

    return generic_list_json(request, Notification, ['creation_date', 'key', 'linked_object', 'pk', 'pk'], 'notifications/center/json.html', bonus_filter_function=bonus_filter)


@login_required
def mark_as_read(request):
    """Display the downdown menu for notificatoins"""

    notification = get_object_or_404(Notification, pk=request.GET.get('pk'), user=request.user)
    notification.seen = True
    notification.seen_date = now()
    notification.save()

    return HttpResponse('')
