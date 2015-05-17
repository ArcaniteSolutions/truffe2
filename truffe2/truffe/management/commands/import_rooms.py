# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.timezone import now


import datetime
import pytz
import json
import sys


from units.models import Unit
from users.models import TruffeUser
from logistics.models import Room, RoomReservation, RoomLogging, RoomReservationLogging


class Command(BaseCommand):
    help = 'Import rooms'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        root_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)
        root_user = TruffeUser.objects.first()
        paris_tz = pytz.timezone("Europe/Paris")

        rooms_by_ids = {}

        for rdata in data['rooms']:

            room, created = Room.objects.get_or_create(title=rdata['nom'], description=rdata['description'], unit=root_unit, active=True, allow_externals=rdata['allowExterne'])

            room.save()

            rooms_by_ids[rdata['id']] = room

            if created:
                RoomLogging(who=root_user, what='imported', object=room).save()

        for rdata in data['reservations']:

            try:
                start_date = paris_tz.localize(datetime.datetime.strptime(rdata['de'], '%Y-%m-%d %H:%M:%S'))
                end_date = paris_tz.localize(datetime.datetime.strptime(rdata['a'], '%Y-%m-%d %H:%M:%S'))
                room = rooms_by_ids[rdata['room']]

                creator = TruffeUser.objects.get(username=rdata['creator'])

                if rdata['moderatePlease']:
                    status = '1_asking'
                elif rdata['accepted']:
                    status = '2_online'
                else:
                    status = '0_draft'

                if rdata['unit'] and rdata['unit'] != '!':
                    unit = Unit.objects.get(name=rdata['unit'])
                    external_user = None
                    external_unit = None
                else:
                    external_user = creator
                    external_unit = rdata['forWho']
                    unit = None

                title = u'Réservation truffe 1 #%s' % (rdata['id'],)

                rr, created = RoomReservation.objects.get_or_create(title=title, defaults={'start_date': start_date, 'end_date': end_date, 'room': room, 'status': status, 'unit': unit, 'unit_blank_user': external_user, 'unit_blank_name': external_unit})
                rr.save()

                if created:
                    RoomReservationLogging(who=root_user, what='imported', object=rr).save()
                    RoomReservationLogging(who=creator, what='created', object=rr).save()

            except TruffeUser.DoesNotExist:
                print "Cannot find", rdata['creator']
            except Unit.DoesNotExist:
                print "Cannot find", rdata['unit']
            except Exception as e:
                print e
