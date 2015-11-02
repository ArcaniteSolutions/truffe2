# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.timezone import now


import datetime


from units.models import Unit, AccreditationLog, Accreditation, Role
from users.models import TruffeUser


class Command(BaseCommand):
    help = 'Sync RLC accreds'

    def handle(self, *args, **options):
        """Rules: All users with role AUTO_RLC_COMS_ROLES in commissions or AUTO_RLC_ROOT_ROLES in root unit are given AUTO_RLC_GIVEN_ROLE"""

        rlc_unit = Unit.objects.get(pk=settings.AUTO_RLC_UNIT_PK)
        rlc_role = Role.objects.get(pk=settings.AUTO_RLC_GIVEN_ROLE)
        system_user = TruffeUser.objects.get(pk=settings.SYSTEM_USER_PK)

        valids_accreds = []

        def _do(unit, roles):

            for accred in unit.accreditation_set.filter(end_date=None, role__pk__in=roles):

                rlc_accred, created = Accreditation.objects.get_or_create(unit=rlc_unit, user=accred.user, end_date=None, role=rlc_role, display_name=u'{} {} ({})'.format(settings.AUTO_RLC_TAG, accred.get_role_or_display_name(), unit), no_epfl_sync=False, hidden_in_epfl=True, hidden_in_truffe=True, need_validation=False)

                rlc_accred.renewal_date = accred.renewal_date
                rlc_accred.save()

                if created:
                    AccreditationLog(accreditation=rlc_accred, who=system_user, what='autocreated').save()

                valids_accreds.append(rlc_accred)

        _do(Unit.objects.get(pk=settings.ROOT_UNIT_PK), settings.AUTO_RLC_ROOT_ROLES)

        for unit in Unit.objects.filter(is_commission=True):
            _do(unit, settings.AUTO_RLC_COMS_ROLES)


        for old_accred in Accreditation.objects.filter(end_date=None, unit=rlc_unit, display_name__startswith=settings.AUTO_RLC_TAG).exclude(pk__in=map(lambda u: u.pk, valids_accreds)):

            old_accred.end_date = now()
            old_accred.save()
            AccreditationLog(accreditation=old_accred, who=system_user, what='autodeleted').save()
