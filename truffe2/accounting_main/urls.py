# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_main.views',

    url(r'^accounting/graph/$', 'accounting_graph'),
    url(r'^accounting/errors/send_message/(?P<pk>[0-9]+)$', 'errors_send_message'),

    url(r'^budget/(?P<pk>[0-9,]+)/copy$', 'copy_budget'),
    url(r'^budget/(?P<pk>[0-9,]+)/get_infos$', 'budget_getinfos'),
)
