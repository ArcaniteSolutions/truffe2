# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'notifications.views',

    url(r'^dropdown$', 'dropdown'),
    url(r'^goto/(?P<pk>[0-9]+)$', 'goto'),

    url(r'^center/$', 'notification_center'),
    url(r'^center/keys$', 'notification_keys'),
    url(r'^center/json$', 'notification_json'),
    url(r'^center/restrictions$', 'notification_restrictions'),
    url(r'^center/restrictions/update$', 'notification_restrictions_update'),
    url(r'^read$', 'mark_as_read'),
)
