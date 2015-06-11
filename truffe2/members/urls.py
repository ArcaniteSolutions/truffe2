# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'members.views',

    url(r'^memberset/(?P<pk>[0-9]+)/export$', 'export_members'),
    url(r'^memberset/(?P<pk>[0-9]+)/import$', 'import_members'),
    url(r'^memberset/(?P<pk>[0-9]+)/load_list$', 'load_list'),
    url(r'^memberset/(?P<pk>[0-9]+)/json$', 'membership_list_json'),

    url(r'^membership/(?P<pk>[0-9~]+)/edit$', 'membership_edit'),

)
