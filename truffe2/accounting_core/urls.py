# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_core.views',

    url(r'^accountingyear/(?P<pk>[0-9,]+)/copy$', 'copy_accounting_year'),
)
