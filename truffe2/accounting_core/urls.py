# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_core.views',

    url(r'^accountingyear/(?P<pk>[0-9,]+)/copy$', 'copy_accounting_year'),
    url(r'^accountingyear/(?P<pk>[0-9]+)/cost_centers$', 'pdf_list_cost_centers'),
    url(r'^accountingyear/(?P<pk>[0-9]+)/accounts$', 'pdf_list_accounts'),
    url(r'^accountingyear/(?P<ypk>[0-9]+)/get_leaves_cat$', 'leaves_cat_by_year'),
    url(r'^accountingyear/(?P<ypk>[0-9]+)/get_parents_cat$', 'parents_cat_by_year'),
    url(r'^accountingyear/(?P<ypk>[0-9]+)/get_accounts$', 'accounts_by_year'),
    url(r'^accountingyear/(?P<ypk>[0-9]+)/get_costcenters$', 'costcenters_by_year'),

    url(r'^costcenter/available_list$', 'costcenter_available_list'),
    url(r'^tva/available_list$', 'tva_available_list'),
)
