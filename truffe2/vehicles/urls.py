
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'vehicles.views',

    url(r'^booking/(?P<pk>[0-9]+)/pdf/', 'booking_pdf'),
)
