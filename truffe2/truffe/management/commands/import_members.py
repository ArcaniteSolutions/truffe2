from django.core.management.base import BaseCommand, CommandError
from members.models import MemberSet, Membership
from users.models import TruffeUser
from units.models import Unit, Role

from django.utils.timezone import now
import datetime
import pytz

import json
import sys


class Command(BaseCommand):
    help = 'Import members'

    def handle(self, *args, **options):

        data = json.loads(sys.stdin.read())

        paris_tz = pytz.timezone("Europe/Paris")

        for unit_data in data['data']:
            try:
                unit = Unit.objects.get(id_epfl=unit_data['id_epfl'])
            except:
                print u"Unit not found !! %s (%s)" % (unit_data['name'], unit_data['id_epfl'])
                unit = None

            members_role_data = unit_data['last_members_role']

            if members_role_data:
                try:
                    role = Role.objects.get(id_epfl=members_role_data['id_epfl'])
                except:
                    print u"Role not found !! %s (%s)" % (members_role_data['name'], members_role_data['id_epfl'])
                    role = None
            else:
                role = Role(name="None")  # No role linked

            if unit and role:

                for mset_data in unit_data['membersets']:
                    mset, __ = MemberSet.objects.get_or_create(name=mset_data['name'], unit=unit, handle_fees=True, ldap_visible=False)
                    mset.generates_accred = (role.name == "None")
                    if mset.generates_accred:
                        mset.generated_accred_type = role

                    for mship_data in mset_data['members']:

                        try:
                            user = TruffeUser.objects.get(username=mship_data['sciper'])
                        except:
                            print u"User not found %s, will create..." % (mship_data['sciper'],)
                            user = TruffeUser(username=mship_data['sciper'], is_active=True, first_name=mship_data['first_name'],
                                              last_name=mship_data['last_name'], email=mship_data['email'])
                            user.save()

                        if mship_data['start_date'] == 'None':
                            print 'Membership with start = None oO ? (user %s) ' % user

                        else:
                            mship, __ = Membership.objects.get_or_create(user=user, group=mset)
                            mship.start_date = paris_tz.localize(datetime.datetime.strptime(mship_data['start_date'], '%Y-%m-%d %H:%M:%S'))
                            mship.payed_fees = mship_data['payed_fees']
                            mship.save()
