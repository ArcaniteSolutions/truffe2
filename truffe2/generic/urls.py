# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'generic.views',

    url('check_unit_name', 'check_unit_name'),

)
