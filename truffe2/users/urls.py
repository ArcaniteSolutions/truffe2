# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'users.views',

    url(r'^login$', 'login'),
)


urlpatterns += patterns(
    '',

    url(r'^login/tequila$', 'app.tequila.login'),
)


urlpatterns += patterns(
    'django.contrib.auth.views',

    (r'^logout$', 'logout', {'next_page': '/'}),
)
