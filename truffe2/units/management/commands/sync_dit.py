# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.encoding import smart_str


import csv


from units.models import Unit


class Command(BaseCommand):
    help = 'Sync accreds to DIT server'

    def handle(self, *args, **options):

        with open('/tmp/generateListAccredsForDIT', 'wb') as csvfile:

            writer = csv.writer(csvfile, delimiter='\t')
            writer.writerow(["Scriper", "GroupeId", "RoleId", "botweb", "Prenom", "Nom", "GroupeNom", "RoleNom", "Type"])

            # On travaille par unité
            for u in Unit.objects.filter(deleted=False).exclude(id_epfl=None):

                if not u.id_epfl:
                    continue

                already_accredited = []

                # Toutes les accreds encore valides
                for a in u.accreditation_set.filter(end_date=None).exclude(role__id_epfl=None, no_epfl_sync=True):

                    if not a.role.id_epfl:
                        continue

                    if not a.user.username_is_sciper():
                        continue

                    if a.user in already_accredited:
                        continue

                    already_accredited.append(a.user)

                    writer.writerow([a.user.username.strip(), u.id_epfl, a.role.id_epfl, "False" if a.hidden_in_epfl else "True", smart_str(a.user.first_name), smart_str(a.user.last_name), smart_str(u.name), smart_str(a.role.name), 'Acred'])

                # TODO: Members

        # TODO
        # os.system("scp /tmp/generateListAccredsForDIT collecte@cadibatch.epfl.ch:agepoly/")
