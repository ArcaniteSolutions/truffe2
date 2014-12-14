# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'notifications.views',

    url(r'^dropdown$', 'dropdown'),
    url(r'^goto/(?P<pk>[0-9]+)$', 'goto'),
)


