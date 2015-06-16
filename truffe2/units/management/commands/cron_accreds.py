# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.timezone import now


import datetime


from notifications.utils import notify_people
from units.models import Unit


class Command(BaseCommand):
    help = 'Do accreds timeout-related-stuff who should be done dailly'

    def handle(self, *args, **options):

        days_before_warnings = [30, 15, 7, 3, 2, 1]

        # On travaille par unité
        for u in Unit.objects.filter(deleted=False):

            # Les destinataires
            dest_users = u.users_with_access('INFORMATIQUE', no_parent=True)

            to_warning = {}

            for d in days_before_warnings:
                to_warning[d] = []

            to_delete = []

            # Toutes les accreds encore valides
            for a in u.accreditation_set.filter(end_date=None):

                # Nombre de jours avant l'expiration
                delta = ((a.validation_date + datetime.timedelta(days=365)) - now()).days

                # Faut-il supprimer l'accred ?
                if delta <= 0:
                    a.end_date = now()
                    a.save()

                    to_delete.append(a)

                # Faut-il prévenir les responsables ?
                if delta in days_before_warnings:
                    to_warning[delta].append(a)

            for d in days_before_warnings:
                if to_warning[d]:
                    notify_people(None, 'Accreds.Warning.%s' % (d,), 'accreds_warning', u, dest_users, {'jours': d, 'accreds': map(lambda a: {'pk': a.pk, 'user': str(a.user), 'role': str(a.role)}, to_warning[d])})

            if to_delete:
                notify_people(None, 'Accreds.Deleted.%s' % (d,), 'accreds_deleted', u, dest_users, {'accreds': map(lambda a: {'pk': a.pk, 'user': str(a.user), 'role': str(a.role)}, to_delete)})
