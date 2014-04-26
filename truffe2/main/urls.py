# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'main.views',

    url(r'^$', 'home'),
)
