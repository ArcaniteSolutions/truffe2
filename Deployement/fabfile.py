from fabric.api import *

output.stdout = True

# Config
import config

env.key_filename = config.SSH_KEY

# Import django tools
import django
