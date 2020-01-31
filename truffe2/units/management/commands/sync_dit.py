# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.encoding import smart_str

import csv
import os

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
                for a in u.accreditation_set.filter(end_date=None).exclude(no_epfl_sync=True).order_by('role__order'):

                    if not a.role.id_epfl:
                        continue

                    if not a.user.username_is_sciper():
                        continue

                    if a.user in already_accredited:
                        continue

                    already_accredited.append(a.user)

                    writer.writerow([a.user.username.strip(), u.id_epfl, a.role.id_epfl, "False" if a.hidden_in_epfl else "True", smart_str(a.user.first_name), smart_str(a.user.last_name), smart_str(u.name), smart_str(a.role.name), 'Acred'])

                # Tous les membres encore actifs
                for mset in u.memberset_set.filter(status='1_active', generates_accred=True):
                    role_id = mset.generated_accred_type.id_epfl

                    if not role_id:
                        continue

                    for mship in mset.membership_set.filter(end_date=None):
                        if not mship.user.username_is_sciper():
                            continue

                        if mship.user in already_accredited:
                            continue

                        already_accredited.append(mship.user)

                        writer.writerow([mship.user.username.strip(), u.id_epfl, role_id, "True" if mset.ldap_visible else "False", smart_str(mship.user.first_name), smart_str(mship.user.last_name), smart_str(u.name), smart_str(mset.generated_accred_type.name), 'Membre'])

        os.system("echo put /tmp/generateListAccredsForDIT | sftp collecte@cadibatch.epfl.ch:agepoly/")
