# -*- coding: utf-8 -*-

from django.conf.urls import include, patterns, url
from django.contrib.auth.views import password_reset, password_reset_confirm, password_change


urlpatterns = patterns(
    'users.views',

    url(r'^login$', 'login'),
    url(r'^login_done$', 'login', {'why': 'reset_done'}, name='login_with_rst_done'),
    url(r'^login_cptd$', 'login', {'why': 'reset_completed'}, name='login_with_rst_completed'),
    url(r'^create_external$', 'users_create_external'),
    url(r'password_change_check', 'password_change_check'),
    url(r'password_change/done/$', 'password_change_done', name='password_change_done'),
    url(r'^password_reset/$', password_reset, {'post_reset_redirect': 'login_with_rst_done',
        'from_email': 'nobody@truffe.agepoly.ch'}, name='password_reset'),
    # From Django 1.7 replace previous line with :
    #    'from_email': 'nobody@truffe.agepoly.ch', 'html_email_template_name': '/registration/password_reset_email_html.html'}, name='password_reset'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm, {'post_reset_redirect': 'login_with_rst_completed'}, name='password_reset_completed'),
    url(r'^', include('django.contrib.auth.urls')),

    url(r'^set_body/(?P<mode>[mh\_])$', 'users_set_body'),
    url(r'^users/$', 'users_list'),
    url(r'^users/json$', 'users_list_json'),
    url(r'^users/(?P<pk>[0-9~]+)$', 'users_profile'),
    url(r'^users/(?P<pk>[0-9~]+)/vcard$', 'users_vcard'),
    url(r'^users/(?P<pk>[0-9~]+)/edit$', 'users_edit'),
    url(r'^users/(?P<pk>[0-9~]+)/profile_picture$', 'users_profile_picture'),

    url(r'^myunit/$', 'users_myunit_list'),
    url(r'^myunit/json$', 'users_myunit_list_json'),
    url(r'^myunit/vcard$', 'users_myunit_vcard'),
    url(r'^myunit/pdf/$', 'users_myunit_pdf'),

    url(r'^ldap/search$', 'ldap_search'),

)

urlpatterns += patterns(
    '',

    url(r'^login/tequila$', 'app.tequila.login'),
)


urlpatterns += patterns(
    'django.contrib.auth.views',

    (r'^logout$', 'logout', {'next_page': '/'}),
)
