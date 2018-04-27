# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'logistics.views',

    url('room/search', 'room_search'),
    url('supply/search', 'supply_search'),

    url(r'^loanagreement/(?P<pk>[0-9]+)/pdf/', 'loanagreement_pdf'),
)
