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
from vehicles.models import Provider, Card, VehicleType, Location, Booking, ProviderLogging, CardLogging, VehicleTypeLogging, LocationLogging, BookingLogging


class Command(BaseCommand):
    help = 'Import vehicles'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        root_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)
        root_user = TruffeUser.objects.first()
        paris_tz = pytz.timezone("Europe/Paris")

        providers_by_ids = {}

        for rdata in data['providers']:

            provider, created = Provider.objects.get_or_create(name=rdata['title'], description=rdata['description'])
            provider.save()

            providers_by_ids[rdata['pk']] = provider

            if created:
                ProviderLogging(who=root_user, what='imported', object=provider).save()

        cards_by_ids = {}

        for rdata in data['cards']:

            provider = providers_by_ids[rdata['provider']]

            card, created = Card.objects.get_or_create(name='{} / {}'.format(provider, rdata['number']), number=rdata['number'], description=rdata['description'], provider=provider)
            card.save()

            cards_by_ids[rdata['pk']] = card

            if created:
                CardLogging(who=root_user, what='imported', object=card).save()

        type_by_ids = {}

        for rdata in data['types']:

            provider = providers_by_ids[rdata['provider']]

            type_, created = VehicleType.objects.get_or_create(name=rdata['title'], description=rdata['description'], provider=provider)
            type_.save()

            type_by_ids[rdata['pk']] = type_

            if created:
                VehicleTypeLogging(who=root_user, what='imported', object=type_).save()

        places_by_ids = {}

        for rdata in data['places']:

            place, created = Location.objects.get_or_create(name=rdata['title'], description=rdata['description'], url_location=rdata['url'])
            place.save()

            places_by_ids[rdata['pk']] = place

            if created:
                LocationLogging(who=root_user, what='imported', object=place).save()

        for rdata in data['booking']:

            try:
                start_date = paris_tz.localize(datetime.datetime.strptime(rdata['de'], '%Y-%m-%d %H:%M:%S'))
                end_date = paris_tz.localize(datetime.datetime.strptime(rdata['a'], '%Y-%m-%d %H:%M:%S'))
                provider = providers_by_ids[rdata['provider']]
                card = cards_by_ids[rdata['card']] if rdata['card'] else None
                place = places_by_ids[rdata['place']] if rdata['place'] else None
                type_ = type_by_ids[rdata['type']]

                creator = TruffeUser.objects.get(username=rdata['user'])

                mapping = {
                    'darft': '0_draft',
                    'demander': '1_asking',
                    'valide': '2_online',
                    'refus': '4_deny',
                    'annule': '3_archive',
                }

                if rdata['unit'] and rdata['unit'] != '!':
                    unit = Unit.objects.get(name=rdata['unit'])
                    external_user = None
                    external_unit = None
                else:
                    print "!!!!", rdata['forWho']
                    external_user = creator
                    external_unit = rdata['forWho']
                    unit = None

                if rdata['forWho']:
                    title = u'{} (T1#%s) pour %s' % (rdata['motif'].split('\n')[0], rdata['pk'], rdata['forWho'])
                    unit = root_unit
                else:
                    title = u'{} (T1#%s)' % (rdata['motif'].split('\n')[0], rdata['pk'],)

                booking, created = Booking.objects.get_or_create(title=title, defaults={'start_date': start_date, 'end_date': end_date, 'card': card, 'responsible': creator, 'reason': rdata['motif'], 'remark': rdata['remark'], 'remark_agepoly': rdata['remark_agepoly'], 'status': mapping.get(rdata['status']), 'provider': provider, 'vehicletype': type_, 'location': place, 'unit': unit})
                booking.save()

                if created:
                    BookingLogging(who=root_user, what='imported', object=booking).save()
                    BookingLogging(who=creator, what='created', object=booking).save()

            except TruffeUser.DoesNotExist:
                print "Cannot find", rdata['user']
            except Unit.DoesNotExist:
                print "Cannot find", rdata['unit']
            except Exception as e:
                print e
