# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from users.models import TruffeUser


class Command(BaseCommand):
    help = 'Sync missing users attributes from LDAP'

    def handle(self, *args, **options):

        for user in TruffeUser.objects.all():
            user.update_from_ldap()
