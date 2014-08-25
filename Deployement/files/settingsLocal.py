
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'truffe2',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'truffe2',
        'PASSWORD': '%(mysql_password)s',
        'HOST': '10.7.0.3',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}


# Make this unique, and don't share it with anybody.
SECRET_KEY = '%(secret_key)s'

BROKER_URL = 'amqp://truffe2:%(rabbitmq_password)s@localhost:5672//'

DEBUG = False

RAVEN_CONFIG = {
    'dsn': '%(raven_dsn)s',
}

ACTIVATE_RAVEN = True

ALLOWED_HOSTS = ['truffe2.agepoly.ch', 'truffe.polylan.ch']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
