# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'main.views',

    url(r'^$', 'home'),
    url(r'^get_to_moderate$', 'get_to_moderate'),

    url(r'^link/base$', 'link_base'),
    url(r'^last_100_logging_entries$', 'last_100_logging_entries'),
)
