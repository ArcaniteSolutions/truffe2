# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_main.views',

    url(r'^accounting/graph/$', 'accounting_graph'),
)
