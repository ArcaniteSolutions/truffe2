# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from users.views import UserListJson
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


urlpatterns = patterns(
    'users.views',

    url(r'^login$', 'login'),
    url(r'^set_body/(?P<mode>[mh\_])$', 'users_set_body'),
    url(r'^users/$', 'users_list'),
    url(r'^users/data$', login_required(csrf_exempt(UserListJson.as_view())), name='users.views.users_list_json'),
    url(r'^users/(?P<pk>[0-9~]+)$', 'users_profile'),
    url(r'^users/(?P<pk>[0-9~]+)/vcard$', 'users_vcard'),
    url(r'^users/(?P<pk>[0-9~]+)/edit$', 'users_edit'),
)


urlpatterns += patterns(
    '',

    url(r'^login/tequila$', 'app.tequila.login'),
)


urlpatterns += patterns(
    'django.contrib.auth.views',

    (r'^logout$', 'logout', {'next_page': '/'}),
)
