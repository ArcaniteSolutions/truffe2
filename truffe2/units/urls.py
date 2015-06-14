# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'units.views',

    url(r'^accreds/$', 'accreds_list'),
    url(r'^accreds/json$', 'accreds_list_json'),
    url(r'^accreds/(?P<pk>[0-9~]+)/renew$', 'accreds_renew'),
    url(r'^accreds/(?P<pk>[0-9~]+)/edit$', 'accreds_edit'),
    url(r'^accreds/(?P<pk>[0-9~]+)/delete$', 'accreds_delete'),
    url(r'^accreds/add$', 'accreds_add'),
    url(r'^accreds/search$', 'accreds_search'),
)
