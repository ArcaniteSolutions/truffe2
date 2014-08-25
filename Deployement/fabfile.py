from fabric.api import *

output.stdout = True

# Config
import config

env.key_filename = config.SSH_KEY

if not env.hosts:
    env.hosts = [config.HOST]

# Import django tools
import django
