# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'communication.views',

    url(r'^ecrans$', 'ecrans'),
    url(r'^random_slide$', 'random_slide'),
    url(r'^website_news$', 'website_news'),
)
