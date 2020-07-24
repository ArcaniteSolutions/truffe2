# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'accounting_tools.views',

    url(r'^subvention/(?P<ypk>[0-9]+)/export$', 'export_demands_yearly'),
    url(r'^subvention/export_all$', 'export_all_demands'),

    url(r'^invoice/(?P<pk>[0-9]+)/pdf/', 'invoice_pdf'),
    url(r'^invoice/(?P<pk>[0-9]+)/bvr/', 'invoice_bvr'),

    url(r'^withdrawal/(?P<pk>[0-9]+)/pdf/', 'withdrawal_pdf'),
    url(r'^withdrawal/list/', 'withdrawal_available_list'),
    url(r'^withdrawal/(?P<pk>[0-9]+)/infos/', 'get_withdrawal_infos'),

    url(r'^internaltransfer/(?P<pk>[0-9,]+)/pdf/', 'internaltransfer_pdf'),
    url(r'^expenseclaim/(?P<pk>[0-9]+)/pdf/', 'expenseclaim_pdf'),
    url(r'^cashbook/(?P<pk>[0-9]+)/pdf/', 'cashbook_pdf'),
    
    url(r'^internaltransfer/(?P<pk>[0-9,]+)/csv/', 'internaltransfer_csv'),
    url(r'^expenseclaim/(?P<pk>[0-9,]+)/csv/', 'expenseclaim_csv'),
    url(r'^cashbook/(?P<pk>[0-9,]+)/csv/', 'cashbook_csv'),
)
