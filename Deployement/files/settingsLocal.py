
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
