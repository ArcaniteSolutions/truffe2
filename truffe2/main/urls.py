# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from main.views import HaystackSearchView

urlpatterns = patterns(
    'main.views',

    url(r'^$', 'home'),
    url(r'^get_to_moderate$', 'get_to_moderate'),

    url(r'^link/base$', 'link_base'),
    url(r'^last_100_logging_entries$', 'last_100_logging_entries'),

    url(r'^search/?$', login_required(HaystackSearchView()), name='search_view'),

    url(r'^set_homepage$', 'set_homepage'),
)
