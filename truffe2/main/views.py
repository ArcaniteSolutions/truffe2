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

    news = HomePageNews.objects.filter(status='1_online').order_by('-pk').all()

    news = filter(lambda s: (not s.start_date or s.start_date <= now()) and (not s.end_date or s.end_date >= now()), list(news))

    return render(request, 'main/home.html', {'news': news})


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
