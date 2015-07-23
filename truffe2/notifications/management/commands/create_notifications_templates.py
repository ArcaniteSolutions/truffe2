from django.core.management.base import BaseCommand, CommandError

import os
import shutil


class Command(BaseCommand):
    help = 'Create a new set of template for a given notification key. Need a source template. Syntaxe: new_key base_key'

    def handle(self, *args, **options):

        if len(args) != 2:
            raise CommandError("Need new_key and base_key")

        new_key = '{}.html'.format(args[0])
        base_key = '{}.html'.format(args[1])

        BASE_PATH = 'notifications/templates/notifications/species/'

        for sub_path in ('center/buttons/', 'center/message/', 'mails/', ''):

            source_path = os.path.join(BASE_PATH, sub_path, base_key)
            dest_path = os.path.join(BASE_PATH, sub_path, new_key)

            if not os.path.isfile(source_path):
                print "Source file {} dosen't exists !".format(source_path)
            elif os.path.isfile(dest_path):
                print "Destination file {} already exists !".format(dest_path)
            else:
                print "{} -> {}".format(source_path, dest_path)
                shutil.copyfile(source_paht, dest_path)

