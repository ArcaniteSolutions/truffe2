# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from django.core.cache import cache
import inspect
import copy
import time


class ModelWithRight(object):
    """A basic class for a model with right. Mainly implement the can(RIGHT, user) function and helper functions"""

    class MetaRights(object):
        linked_user_property = 'user'
        linked_unit_property = 'unit'

        rights = {}

        @classmethod
        def rights_update(cls, new_rights):
            cls.rights = copy.deepcopy(cls.rights)
            cls.rights.update(new_rights)

    @classmethod
    def static_rights_can(cls, right, user, unit_to_link=None, year_to_link=None):

        dummy = cls()

        if unit_to_link and hasattr(dummy.MetaRights, 'linked_unit_property') and dummy.MetaRights.linked_unit_property:
            setattr(dummy, dummy.MetaRights.linked_unit_property, unit_to_link)

        if unit_to_link and hasattr(dummy, 'generic_set_dummy_unit'):
            dummy.generic_set_dummy_unit(unit_to_link)

        from accounting_core.utils import AccountingYearLinked

        if year_to_link and isinstance(dummy, AccountingYearLinked):
            dummy.accounting_year = year_to_link

        return dummy.rights_can(right, user)

    def rights_expire(self):
        """Mark cache as invalid"""
        cache_key_last = 'right~last_%s.%s_%s' % (inspect.getmodule(self).__name__, self.__class__.__name__, self.pk or 'DUMMY')
        cached_last = time.time()
        cache.set(cache_key_last, cached_last)

    def rights_can(self, right, user):

        from accounting_core.utils import AccountingYearLinked

        if right not in self.MetaRights.rights or not hasattr(self, 'rights_can_%s' % (right,)):
            return False

        if user.is_superuser:
            return True

        if not user.pk:
            return False

        # A cache system is used, for performances

        # To be able to clear cache, a timestamp is also cached with the lasted
        # modification on the object (cache_key_last) and on user's rights
        # (cache_key_user_last). If the computed value is olded than those two
        # values, cache is not taken into account

        if hasattr(self, 'unit') and self.unit and self.unit.pk:
            unit_pk = self.unit.pk
        else:
            unit_pk = 'NOUPK'

        if isinstance(self, AccountingYearLinked):
            try:
                accounting_year_pk = self.accounting_year.pk
            except:
                accounting_year_pk = 'NOYPK'
        else:
            accounting_year_pk = 'NOYPK'

        cache_key = 'right_%s.%s_%s_%s_%s_%s_%s' % (inspect.getmodule(self).__name__, self.__class__.__name__, self.pk or 'DUMMY', user.pk, right, unit_pk, accounting_year_pk)
        cache_key_last = 'right~last_%s.%s_%s' % (inspect.getmodule(self).__name__, self.__class__.__name__, self.pk or 'DUMMY')
        cache_key_user_last = 'right~user_%s' % (user.pk, )

        cached_value = cache.get(cache_key)

        cached_last = cache.get(cache_key_last)
        cached_user_last = cache.get(cache_key_user_last)

        current_time = time.time()

        if cached_last is None:
            cached_last = current_time
            cache.set(cache_key_last, cached_last)

        if cached_user_last is None:
            cached_user_last = current_time
            cache.set(cache_key_user_last, cached_user_last)

        if cached_value is not None:
            (cached_value_last, cached_value) = cached_value
            if cached_value_last < cached_last or cached_value_last < cached_user_last:
                cached_value = None

        if cached_value is None or settings.DEBUG:
            cached_value = getattr(self, 'rights_can_%s' % (right,))(user)
            cache.set(cache_key, (cached_last, cached_value), 600)

        return cached_value

    def rights_is_linked_user(self, user):
        if not self.MetaRights.linked_user_property or not hasattr(self, self.MetaRights.linked_user_property):
            return False

        return getattr(self, self.MetaRights.linked_user_property) == user

    def rights_in_unit(self, user, unit, access=None, no_parent=False):
        return unit.is_user_in_groupe(user, access, no_parent=no_parent)

    def rights_in_linked_unit(self, user, access=None):
        if not self.MetaRights.linked_unit_property or not hasattr(self, self.MetaRights.linked_unit_property):
            return False

        unit = getattr(self, self.MetaRights.linked_unit_property)

        if not unit:
            e = Exception("Tried to test right in unit without an unit")
            raise e
            return False

        if type(access) is list:
            for acc in access:
                if self.rights_in_unit(user, unit, acc):
                    return True
            return False

        return self.rights_in_unit(user, unit, access)

    def rights_in_root_unit(self, user, access=None):
        from units.models import Unit

        unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

        if type(access) is list:
            for acc in access:
                if self.rights_in_unit(user, unit, acc):
                    return True
            return False

        return self.rights_in_unit(user, unit, access)

    def people_in_unit(self, unit, access=None, no_parent=False):
        return unit.users_with_access(access, no_parent=no_parent)

    def people_in_linked_unit(self, access=None):

        if not self.MetaRights.linked_unit_property or not hasattr(self, self.MetaRights.linked_unit_property):
            return False

        unit = getattr(self, self.MetaRights.linked_unit_property)

        return self.people_in_unit(unit, access)

    def people_in_root_unit(self, access=None):

        from units.models import Unit

        return self.people_in_unit(Unit.objects.get(pk=settings.ROOT_UNIT_PK), access)


class BasicRightModel(ModelWithRight):

    class MetaRights(ModelWithRight.MetaRights):
        pass

    def __init__(self, *args, **kwargs):
        super(BasicRightModel, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'LIST': _(u'Peut lister les éléments'),
            'SHOW': _(u'Peut afficher cet élément'),
            'EDIT': _(u'Peut modifier cet élément'),
            'DELETE': _(u'Peut supprimer cet élément'),
            'RESTORE': _(u'Peut restaurer un élément'),
            'CREATE': _(u'Peut créer un élément'),
            'DISPLAY_LOG': _(u'Peut afficher les logs de l\'élément'),
        })

    def rights_can_LIST(self, user):
        return self.rights_can_SHOW(user)

    def rights_can_SHOW(self, user):
        return False

    def rights_can_EDIT(self, user):
        return False

    def rights_can_DELETE(self, user):
        return self.rights_can_EDIT(user)

    def rights_can_RESTORE(self, user):
        return self.rights_can_EDIT(user)

    def rights_can_CREATE(self, user):
        return self.rights_can_EDIT(user)

    def rights_can_DISPLAY_LOG(self, user):
        return self.rights_can_EDIT(user)


class AgepolyEditableModel(BasicRightModel):

    class MetaRights(BasicRightModel.MetaRights):
        pass

    class MetaRightsAgepoly:
        access = 'PRESIDENCE'
        world_ro_access = False

    def rights_can_SHOW(self, user):
        return self.MetaRightsAgepoly.world_ro_access or self.rights_in_root_unit(user, self.MetaRightsAgepoly.access)

    def rights_can_EDIT(self, user):
        return self.rights_in_root_unit(user, self.MetaRightsAgepoly.access)

    def rights_peoples_in_EDIT(self):
        return self.people_in_root_unit(self.MetaRightsAgepoly.access)


class UnitEditableModel(BasicRightModel):
    """Editable par n'importe quelle unit, pour les objects de l'unité"""

    class MetaRights(BasicRightModel.MetaRights):
        pass

    class MetaRightsUnit:
        access = 'PRESIDENCE'
        unit_ro_access = False

    def rights_can_SHOW(self, user):

        if not hasattr(self, self.MetaRights.linked_unit_property):
            # Check if at least one of unit match
            for accred in user.accreditation_set.filter(end_date=None):
                setattr(self, self.MetaRights.linked_unit_property, accred.unit)
                if self.rights_can_SHOW(user):
                    return True
            return False

        return (self.MetaRightsUnit.unit_ro_access and self.rights_in_linked_unit(user)) or self.rights_in_linked_unit(user, self.MetaRightsUnit.access)

    def rights_can_EDIT(self, user):
        return self.rights_in_linked_unit(user, self.MetaRightsUnit.access)

    def rights_peoples_in_EDIT(self):
        return self.people_in_linked_unit(self.MetaRightsUnit.access)


class UnitExternalEditableModel(BasicRightModel):
    """Editable par n'importe quelle unit, y compris les externes pour les objects de l'unité"""

    class MetaRights(BasicRightModel.MetaRights):
        pass

    class MetaRightsUnit:
        access = 'PRESIDENCE'
        unit_ro_access = False

    def rights_can_SHOW(self, user):

        # Peut toujours afficher, de manière générique
        if not hasattr(self, self.MetaRights.linked_unit_property):
            return True

        if not getattr(self, self.MetaRights.linked_unit_property):  # Pas d'unité. L'user doit être l'user
            try:
                return not self.unit_blank_user or self.unit_blank_user == user
            except:
                return True  # Pas d'unité, ni d'users

        return (self.MetaRightsUnit.unit_ro_access and self.rights_in_linked_unit(user)) or self.rights_in_linked_unit(user, self.MetaRightsUnit.access)

    def rights_can_EDIT(self, user):

        if not getattr(self, self.MetaRights.linked_unit_property):  # Pas d'unité. L'user doit être l'user
            try:
                return not self.unit_blank_user or self.unit_blank_user == user
            except:
                return True  # Pas d'unité, ni d'users

        return self.rights_in_linked_unit(user, self.MetaRightsUnit.access)

    def rights_peoples_in_EDIT(self):

        if not getattr(self, self.MetaRights.linked_unit_property):  # Pas d'unité. L'user doit être l'user
            return [user]

        return self.people_in_linked_unit(self.MetaRightsUnit.access)
