# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'members.views',

    url(r'^memberset/(?P<pk>[0-9]+)/export$', 'export_members'),
    url(r'^memberset/(?P<pk>[0-9]+)/import$', 'import_members'),
    url(r'^memberset/(?P<pk>[0-9]+)/import_list$', 'import_members_list'),
    url(r'^memberset/(?P<pk>[0-9]+)/json$', 'membership_list_json'),
    url(r'^memberset/(?P<pk>[0-9]+)/add$', 'membership_add'),

    url(r'^membership/(?P<pk>[0-9]+)/delete$', 'membership_delete'),
    url(r'^membership/(?P<pk>[0-9~]+)/toggle_fees$', 'membership_toggle_fees'),

)
