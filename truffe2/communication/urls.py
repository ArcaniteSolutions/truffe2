# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'communication.views',

    url(r'^ecrans$', 'ecrans'),
    url(r'^random_slide$', 'random_slide'),
    url(r'^website_news$', 'website_news'),
    url(r'^logo_public_list$', 'logo_public_list'),
    url(r'^logo_public_load$', 'logo_public_load'),
)
