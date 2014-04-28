# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'users.views',

    url(r'^login$', 'login'),
    url(r'^users/(?P<pk>[0-9]+)$', 'users_profile'),
    url(r'^users/(?P<pk>[0-9]+)/edit$', 'users_edit'),
)


urlpatterns += patterns(
    '',

    url(r'^login/tequila$', 'app.tequila.login'),
)


urlpatterns += patterns(
    'django.contrib.auth.views',

    (r'^logout$', 'logout', {'next_page': '/'}),
)
