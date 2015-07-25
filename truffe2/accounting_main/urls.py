# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_main.views',

    url(r'^accounting/graph/$', 'accounting_graph'),
    url(r'^accounting/errors/send_message/(?P<pk>[0-9]+)$', 'errors_send_message'),

    url(r'^accounting/import/step/0$', 'accounting_import_step0'),
    url(r'^accounting/import/step/1/(?P<key>[0-9\-a-f]+)$', 'accounting_import_step1'),
)
