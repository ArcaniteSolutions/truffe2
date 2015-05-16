# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'logistics.views',

    url('room/search', 'room_search'),
    url('supply/search', 'supply_search'),

)
