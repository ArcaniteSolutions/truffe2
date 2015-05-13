# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'main.views',

    url(r'^$', 'home'),
    url(r'^get_to_moderate$', 'get_to_moderate'),
)
