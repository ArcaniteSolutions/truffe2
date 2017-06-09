# -*- coding: utf-8 -*-

# Django settings for truffe2 project.

from django.utils.translation import ugettext_lazy as _

from os.path import abspath, dirname, join, normpath
DJANGO_ROOT = dirname(abspath(__file__)) + '/../'


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-ch'

LANGUAGES = (
    ('en-us', _(u'Anglais')),
    ('fr-ch', _(u'Français')),
)

LOCALE_PATHS = (
    normpath(join(DJANGO_ROOT, 'locale')) + '/',
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = normpath(join(DJANGO_ROOT, 'media')) + '/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = normpath(join(DJANGO_ROOT, 'static')) + '/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'app.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'app.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    normpath(join(DJANGO_ROOT, 'templates')) + '/'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'south',
    'bootstrap3',
    'impersonate',
    'multiselectfield',
    'easy_thumbnails',
    'jfu',
    'haystack',
    'celery_haystack',

    'truffe',

    'main',
    'users',
    'units',
    'rights',
    'communication',
    'notifications',
    'logistics',
    'accounting_core',
    'accounting_main',
    'accounting_tools',

    'members',
    'vehicles',

    'generic',

)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

ACTIVATE_RAVEN = False

AUTH_USER_MODEL = 'users.TruffeUser'

AUTHENTICATION_BACKENDS = ('app.tequila.Backend',)
LOGIN_URL = '/users/login'

TEQUILA_SERVER = 'https://tequila.epfl.ch'  # Url of tequila server
TEQUILA_SERVICE = 'Truffe2 - L\'intranet de l\'AGEPoly'  # Title used in tequila
TEQUILA_AUTOCREATE = True  # Auto create users ?
TEQUILA_FAILURE = '/users/login'  # Where to redirect user if there is a problem

LOGIN_REDIRECT_URL = '/'

BOOTSTRAP3 = {
    'jquery_url': '//code.jquery.com/jquery.min.js',
    'base_url': '//netdna.bootstrapcdn.com/bootstrap/3.0.3/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'horizontal_label_class': 'col-md-2',
    'horizontal_field_class': 'col-md-10',
}

IMPERSONATE_REQUIRE_SUPERUSER = True

DATETIME_FORMAT = "d.m.Y H:i:s"
USE_TZ = True

TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "app.utils.add_current_unit",
    "app.utils.add_current_year",
    "notifications.views.notifications_count",
)

LDAP = 'ldap://ldap.epfl.ch:389'

ROOT_UNIT_PK = 1
SYSTEM_USER_PK = 1572
PRESIDENT_ROLE_PK = 1
CS_ACCOUNT_NUMBER = "1020 -"  # Label of account for Credit Suisse


AUTO_RLC_UNIT_PK = 7  # The EPFL "Acces RLC" unit truffe's pk
AUTO_RLC_TAG = u"[Auto]"  # The tag to identify our accreds
AUTO_RLC_COMS_ROLES = [1, 3]  # The roles used to give access for commissions
AUTO_RLC_ROOT_ROLES = [1, ]  # The roles used to give access for root unit
AUTO_RLC_GIVEN_ROLE = 15


SOUTH_MIGRATION_MODULES = {
    'easy_thumbnails': 'easy_thumbnails.south_migrations',
}

SENDFILE_BACKEND = 'sendfile.backends.simple'


THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'app.utils.pad_image',
    'easy_thumbnails.processors.autocrop',
    'easy_thumbnails.processors.scale_and_crop',
    'easy_thumbnails.processors.filters',
)

NOTIFS_MAXIMUM_WAIT = 15  # En minutes, le temps maximal avant d'envoyer une notification
NOTIFS_MINIMUM_BLANK = 5  # En minutes, le temps minimal sans notification avant d'envoyer une notification

FORMAT_MODULE_PATH = 'app.formats'


HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': join(DJANGO_ROOT, 'whoosh_index'),
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 25
HAYSTACK_MAX_SIMPLE_SEARCH_RESULTS = 100

WEBSITE_PATH = 'https://truffe2.agepoly.ch'

EMAIL_FROM = 'truffe2@epfl.ch'

try:
    from settingsLocal import *
except ImportError:
    raise

if ACTIVATE_RAVEN:
    INSTALLED_APPS = INSTALLED_APPS + (
        'raven.contrib.django.raven_compat',
    )
