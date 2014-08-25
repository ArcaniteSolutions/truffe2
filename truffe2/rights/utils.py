# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from django.core.cache import cache
import inspect
import copy


class ModelWithRight(object):
    """A basic class for a model with right. Mainly implement the can(RIGHT, user) function and helper functions"""

    class MetaRights:
        linked_user_property = 'user'
        linked_unit_property = 'unit'

        rights = {}

        @classmethod
        def rights_update(cls, new_rights):
            cls.rights = copy.deepcopy(cls.rights)
            cls.rights.update(new_rights)

    @classmethod
    def static_rights_can(cls, right, user, unit_to_link=None):

        dummy = cls()

        if unit_to_link:
            setattr(dummy, dummy.MetaRights.linked_unit_property, unit_to_link)

        return dummy.rights_can(right, user)

    def rights_can(self, right, user):

        if right not in self.MetaRights.rights or not hasattr(self, 'rights_can_%s' % (right,)):
            return False

        if user.is_superuser:
            return True

        cache_key = 'right_%s.%s_%s_%s_%s' % (inspect.getmodule(self).__name__, self.__class__.__name__, self.pk or 'DUMMY', user.pk, right)

        cached_value = cache.get(cache_key)

        cached_value = None

        if cached_value is None:
            cached_value = getattr(self, 'rights_can_%s' % (right,))(user)
            cache.set(cache_key, cached_value, 600)

        return cached_value

    def rights_is_linked_user(self, user):
        if not self.MetaRights.linked_user_property or not hasattr(self, self.MetaRights.linked_user_property):
            return False

        return getattr(self, self.MetaRights.linked_user_property) == user

    def rights_in_linked_unit(self, user, access=None):
        if not self.MetaRights.linked_unit_property or not hasattr(self, self.MetaRights.linked_unit_property):
            return False

        unit = getattr(self, self.MetaRights.linked_unit_property)

        if not unit:
            e = Exception("Tried to test right in unit without an unit")
            print e
            raise e
            return False

        return unit.is_user_in_groupe(user, access)

    def rights_in_root_unit(self, user, access=None):
        from units.models import Unit

        return Unit.objects.get(pk=settings.ROOT_UNIT_PK).is_user_in_groupe(user, access)


class BasicRightModel(ModelWithRight):

    class MetaRights(ModelWithRight.MetaRights):
        pass

    def __init__(self, *args, **kwargs):
        super(BasicRightModel, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'LIST': _(u'Peut lister les éléments'),
            'SHOW': _(u'Peut afficher cet éléments'),
            'EDIT': _(u'Peut modifier cet éléments'),
            'DELETE': _(u'Peut supprimer cet éléments'),
            'RESTORE': _(u'Peut restaurer un élément'),
            'CREATE': _(u'Peut créer un élément'),
            'DISPLAY_LOG': _(u'Peut afficher les logs de élément'),
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


class UnitEditableModel(BasicRightModel):

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
