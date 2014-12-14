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


def goto(request, pk):

    notification = get_object_or_404(Notification, pk=pk, user=request.user)

    notification.seen = True
    notification.seen_date = now()
    notification.save()

    return HttpResponseRedirect(request.GET.get('next'))


def notifications_count(request):

    if request.user.pk:
        notifications = Notification.objects.filter(user=request.user, seen=False)
        return {'notifications_count': notifications.count()}
    else:
        return {'notifications_count': 0}
