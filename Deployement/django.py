from fabric.api import *
from fabric.contrib.files import upload_template, append, comment

import uuid

import config


@task
def move_www_home():
    """Move home of www-data to /home"""
    sudo("mkdir /home/www-data")
    sudo("chown www-data:www-data /home/www-data")
    sudo("service apache2 stop")
    sudo("usermod -d /home/www-data www-data")
    sudo("service apache2 start")


@task
def install_apache():
    """Install apache"""
    sudo('apt-get -y install apache2 libapache2-mod-wsgi')


@task
def configure_apache():
    """Configure apache"""
    # Disable default site
    sudo('a2dissite 000-default')

    # Copy config
    upload_template('files/apache.conf', '/etc/apache2/sites-available/apache.conf', {})

    # Enable config
    sudo('a2ensite apache.conf', pty=True)


@task
def restart_apache():
    """Restart apache"""
    sudo('service apache2 restart')


@task
def install_rabbitmq():
    """Install rabbitmq"""
    sudo('apt-get -y install rabbitmq-server')


@task
def configure_rabbitmq():
    """Configure rabbitmq"""

    # Enable webpluging
    sudo('rabbitmq-plugins enable rabbitmq_management')

    # Setup admin user
    sudo('rabbitmqctl add_user admin ' + config.ADMIN_PASSWORD)
    sudo('rabbitmqctl set_user_tags admin administrator')
    sudo('rabbitmqctl set_permissions admin .\* .\* .\*')

    # Setup truffe2 user
    sudo('rabbitmqctl add_user truffe2 ' + config.RABBITMQ_PASSWORD)
    sudo('rabbitmqctl set_permissions truffe2 .\* .\* .\*')

    # Disable guest user
    sudo('rabbitmqctl delete_user guest')

    # Restart rabbitmq
    sudo('service rabbitmq-server restart')


@task
def install_mysql():
    """Install mysql"""

    # First, setup root password
    sudo('apt-get install -y debconf-utils')

    debconf_defaults = [
        "mysql-server-5.5 mysql-server/root_password_again password %s" % (config.ADMIN_PASSWORD,),
        "mysql-server-5.5 mysql-server/root_password password %s" % (config.ADMIN_PASSWORD,),
    ]

    sudo("echo '%s' | debconf-set-selections" % "\n".join(debconf_defaults))

    sudo("apt-get -y install mysql-server")


@task
def configure_mysql():
    """Configure mysql"""

    def mysql_execute(sql):
        """Executes passed sql command using mysql shell."""

        sql = sql.replace('"', r'\"')
        return run('echo "%s" | mysql --user="root" --password="%s"' % (sql, config.ADMIN_PASSWORD))

    mysql_execute("CREATE DATABASE truffe2 DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;")
    mysql_execute("CREATE USER 'truffe2'@'localhost' IDENTIFIED BY '%s';" % (config.MYSQL_PASSWORD,))
    mysql_execute("GRANT ALL ON truffe2.* TO 'truffe2'@'localhost'; FLUSH PRIVILEGES;")


@task
def install_python():
    """Install python and python deps"""
    sudo('apt-get install -y python-crypto python-mysqldb python-imaging python-pip python python-dev python-ldap python-memcache')
    sudo('apt-get install -y python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox')


@task
def install_git():
    """Install git"""
    sudo('apt-get install -y git')


@task
def install_memcache():
    """Install git"""
    sudo('apt-get install -y memcached')


@task
def clone_repo():
    """Clone the git repository"""

    sudo('mkdir -p /var/www/git-repo')

    with cd('/var/www/git-repo'):
        sudo('git clone ssh://git@dit.polylan.ch:1025/agepoly/truffe2.git truffe2')


@task
def pull_repos():
    """Pull the git repository"""

    with cd('/var/www/git-repo/truffe2'):
        sudo('git pull')


@task
def install_pip_dep():
    """Install python depenencies using pip"""

    sudo('pip install -r /var/www/git-repo/truffe2/truffe2/data/pip-reqs.txt')


@task
def install_supervisor():
    """Install supervisor"""
    sudo('apt-get install -y supervisor')


@task
def chmod_and_chown():
    """Update folder rights"""
    with cd('/var/www/git-repo'):
        sudo("chown -R www-data:www-data .")

    with cd('/var/log/apache2/'):
        sudo('chown www-data:www-data .')
        sudo('touch django.log')
        sudo("chmod 777 *")


@task
def sync_databases():
    """Sync django databases"""
    with cd('/var/www/git-repo/truffe2/truffe2'):
        sudo("python manage.py syncdb --noinput")
        sudo("python manage.py migrate --noinput")


@task
def collect_statics():
    """Collect statics"""
    with cd('/var/www/git-repo/truffe2/truffe2'):
        sudo("python manage.py collectstatic --noinput")


@task
def start_celery():
    """Start celery deamon"""
    with cd('/var/www/git-repo/truffe2/truffe2'):
        sudo('su www-data -c "supervisord -c data/supervisord.conf"')


@task
def stop_celery():
    """Stop celery deamon"""
    with cd('/var/www/git-repo/truffe2/truffe2'):
        sudo('su www-data -c "supervisorctl -c data/supervisord.conf shutdown"')


@task
def configure_truffe():
    """Configure the django application"""
    upload_template('files/settingsLocal.py', '/var/www/git-repo/truffe2/truffe2/app/settingsLocal.py', {
        'mysql_password': config.MYSQL_PASSWORD,
        'secret_key': str(uuid.uuid4()),
        'rabbitmq_password': config.RABBITMQ_PASSWORD,
        'raven_dsn': config.RAVEN_DSN,
    })


@task
def update_code():
    """Update code"""

    # execute(stop_celery)
    execute(pull_repos)
    execute(install_pip_dep)
    execute(collect_statics)
    execute(chmod_and_chown)
    execute(configure_truffe)
    execute(sync_databases)
    execute(restart_apache)
    # execute(start_celery)


@task
def deploy_new():
    """Deploy a new server"""

    execute(install_apache)
    execute(move_www_home)
    execute(configure_apache)

    execute(install_rabbitmq)
    execute(configure_rabbitmq)

    # execute(install_mysql)
    # execute(configure_mysql)

    execute(install_git)
    execute(clone_repo)

    execute(install_memcache)

    execute(install_python)
    execute(install_pip_dep)

    execute(install_supervisor)

    execute(configure_truffe)

    execute(chmod_and_chown)

    execute(sync_databases)

    execute(start_celery)

    execute(restart_apache)
