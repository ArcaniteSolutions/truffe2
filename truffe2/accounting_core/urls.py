# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_core.views',

    url(r'^accountingyear/(?P<pk>[0-9,]+)/copy$', 'copy_accounting_year'),

    url(r'^costcenter/available_list$', 'costcenter_available_list'),
    url(r'^tva/available_list$', 'tva_available_list'),
    url(r'^accountingyear/(?P<pk>[0-9]+)/cost_centers$', 'pdf_list_cost_centers'),
    url(r'^accountingyear/(?P<pk>[0-9]+)/accounts$', 'pdf_list_accounts'),
)
