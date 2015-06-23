from django.core.management.base import BaseCommand, CommandError
from units.models import Unit, Role, Accreditation

import json


class Command(BaseCommand):
    help = 'Dump accreds'

    def handle(self, *args, **options):

        retour = []

        for unit in Unit.objects.all():

            accreds = []

            for accred in unit.accreditation_set.all():
                accreds.append({'user': accred.user.username, 'role': accred.role.name, 'start': str(accred.start_date), 'end': str(accred.end_date), 'customName': accred.display_name})

            data = {'name': unit.name, 'accreds': accreds}

            retour.append(data)

        print json.dumps({'data': retour})
