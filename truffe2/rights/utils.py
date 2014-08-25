# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from django.core.cache import cache
import inspect


class ModelWithRight(object):
    """A basic class for a model with right. Mainly implement the can(RIGHT, user) function and helper functions"""

    class MetaRights:
        linked_user_property = 'user'
        linked_unit_property = 'unit'

        rights = {}

    @classmethod
    def static_rights_can(cls, right, user):

        dummy = cls()

        return dummy.rights_can(right, user)

    def rights_can(self, right, user):

        if right not in self.MetaRights.rights or not hasattr(self, 'rights_can_%s' % (right,)):
            return False

        if user.is_superuser:
            return True

        cache_key = 'right_%s.%s_%s_%s_%s' % (inspect.getmodule(self).__name__, self.__class__.__name__, self.pk or 'DUMMY', user.pk, right)

        cached_value = cache.get(cache_key)

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

        return getattr(self, self.MetaRights.linked_user_property).is_user_in_groupe(user, access)

    def rights_in_root_unit(self, user, access=None):
        from units.models import Unit

        return Unit.objects.get(pk=settings.ROOT_UNIT_PK).is_user_in_groupe(user, access)


class BasicRightModel(ModelWithRight):

    class MetaRights(ModelWithRight.MetaRights):
        pass

    def __init__(self, *args, **kwargs):
        super(BasicRightModel, self).__init__(*args, **kwargs)

        self.MetaRights.rights.update({
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

    class MetaRightsAgepoly:
        access = 'PRESIDENCE'
        world_ro_access = False

    def rights_can_SHOW(self, user):
        return self.MetaRightsAgepoly.world_ro_access or self.rights_in_root_unit(user, self.MetaRightsAgepoly.access)

    def rights_can_EDIT(self, user):
        return self.rights_in_root_unit(user, self.MetaRightsAgepoly.access)
