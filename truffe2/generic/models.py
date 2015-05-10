# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns, url

import json
import copy
import inspect
import importlib
from pytz import timezone

from users.models import TruffeUser
from generic import views
from generic.forms import GenericForm
from app.utils import get_property
from notifications.utils import notify_people, unotify_people


class FalseFK():

    def __init__(self, model, *args, **kwargs):
        self.model = model
        self.args = args
        self.kwargs = kwargs


def build_models_list_of(Class):
    retour = []
    already_returned = []
    for app in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(app)
            models_module = importlib.import_module('.models', app)
            views_module = importlib.import_module('.views', app)
            urls_module = importlib.import_module('.urls', app)
            forms_module = importlib.import_module('.forms', app)
        except Exception as e:
            continue

        clsmembers = inspect.getmembers(models_module, inspect.isclass)

        for model_name, model_class in clsmembers:
            if issubclass(model_class, Class) and model_class != Class and model_class not in already_returned:

                data = (module, (views_module, urls_module, models_module, forms_module), model_class)

                # Special case for unit, who must be loaded first
                if model_name in ['_Unit', '_Role']:
                    retour.insert(0, data)
                else:
                    retour.append(data)

                already_returned.append(model_class)

    return retour


class GenericModel(models.Model):
    """Un modele generic pour truffe"""

    deleted = models.BooleanField(default=False)

    @staticmethod
    def startup():
        """Execute code at startup"""

        classes = build_models_list_of(GenericModel)

        cache = {}

        for module, (views_module, urls_module, models_module, forms_module), model_class in classes:

            if model_class.__name__[0] != '_':
                continue

            # Create the new model
            extra_data = {'__module__': models_module.__name__}

            if issubclass(model_class, GenericStateModel):
                extra_data.update(GenericStateModel.do(module, models_module, model_class, cache))

            if issubclass(model_class, GenericExternalUnitAllowed):
                extra_data.update(GenericExternalUnitAllowed.do(module, models_module, model_class, cache))

            for key, value in model_class.__dict__.iteritems():
                if hasattr(value, '__class__') and value.__class__ == FalseFK:
                    extra_data.update({key: models.ForeignKey(cache[value.model], *value.args, **value.kwargs)})

            real_model_class = type(model_class.__name__[1:], (model_class,), extra_data)

            setattr(models_module, real_model_class.__name__, real_model_class)

            cache['%s.%s' % (models_module.__name__, real_model_class.__name__)] = real_model_class

            # Add the logging model
            logging_class = type(real_model_class.__name__ + 'Logging', (GenericLogEntry,), {'object': models.ForeignKey(real_model_class, related_name='logs'), '__module__': models_module.__name__})
            setattr(models_module, logging_class.__name__, logging_class)

            # Create the form module
            def generate_meta(Model):
                class Meta():
                    model = Model
                    exclude = ('deleted', 'status')

                class MetaNoUnit():
                    model = Model
                    exclude = ('deleted', 'status', 'unit')

                class MetaNoUnitExternal():
                    model = Model
                    exclude = ('deleted', 'status', 'unit', 'unit_blank_user')

                if hasattr(model_class.MetaData, 'has_unit') and model_class.MetaData.has_unit:
                    if issubclass(model_class, GenericExternalUnitAllowed):
                        return MetaNoUnitExternal
                    return MetaNoUnit

                return Meta

            form_model_class = type(real_model_class.__name__ + 'Form', (GenericForm,), {'Meta': generate_meta(real_model_class)})
            setattr(forms_module, form_model_class.__name__, form_model_class)

            # Add views
            base_views_name = real_model_class.__name__.lower()

            if not hasattr(views_module, base_views_name + '_list'):

                setattr(views_module, base_views_name + '_list', views.generate_list(module, base_views_name, real_model_class))
                setattr(views_module, base_views_name + '_list_json', views.generate_list_json(module, base_views_name, real_model_class))
                setattr(views_module, base_views_name + '_edit', views.generate_edit(module, base_views_name, real_model_class, form_model_class, logging_class))
                setattr(views_module, base_views_name + '_show', views.generate_show(module, base_views_name, real_model_class, logging_class))
                setattr(views_module, base_views_name + '_delete', views.generate_delete(module, base_views_name, real_model_class, logging_class))
                setattr(views_module, base_views_name + '_deleted', views.generate_deleted(module, base_views_name, real_model_class, logging_class))
                setattr(views_module, base_views_name + '_contact', views.generate_contact(module, base_views_name, real_model_class, logging_class))

                # Add urls to views
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^' + base_views_name + '/$', base_views_name + '_list'),
                    url(r'^' + base_views_name + '/json$', base_views_name + '_list_json'),
                    url(r'^' + base_views_name + '/deleted$', base_views_name + '_deleted'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9~]+)/edit$', base_views_name + '_edit'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/delete$', base_views_name + '_delete'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/contact/(?P<key>.+)$', base_views_name + '_contact'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/$', base_views_name + '_show'),
                )

                setattr(real_model_class, '_show_view', '%s.%s_show' % (views_module.__name__, base_views_name,))

            if issubclass(model_class, GenericStateModel):
                setattr(views_module, base_views_name + '_switch_status', views.generate_switch_status(module, base_views_name, real_model_class, logging_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/switch_status$', base_views_name + '_switch_status'),
                )
            if issubclass(model_class, GenericStateUnitValidable):
                setattr(views_module, base_views_name + '_list_related', views.generate_list_related(module, base_views_name, real_model_class))
                setattr(views_module, base_views_name + '_list_related_json', views.generate_list_related_json(module, base_views_name, real_model_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^' + base_views_name + '/related/$', base_views_name + '_list_related'),
                    url(r'^' + base_views_name + '/related/json$', base_views_name + '_list_related_json'),
                )

    def build_state(self):
        """Return the current state of the object. Used for diffs."""
        retour = {}
        opts = self._meta
        for f in sorted(opts.fields + opts.many_to_many):
            if isinstance(f, models.DateTimeField):
                if not getattr(self, f.name):
                    retour[f.name] = None
                else:
                    loc = getattr(self, f.name).astimezone(timezone('Europe/Berlin'))
                    retour[f.name] = loc.strftime("%Y-%m-%d %H:%M:%S")

            else:
                retour[f.name] = unicode(getattr(self, f.name))

        return retour

    def last_log(self):
        """Return the last log entry"""
        return self.logs.order_by('-when')[0]

    def display_url(self):
        return reverse(str(self.__class__._show_view), args=(self.pk,))

    class Meta:
        abstract = True


class GenericStateModel(object):
    """Un modele generic avec une notiion de status"""

    @staticmethod
    def do(module, models_module, model_class, cache):
        """Execute code at startup"""

        return {'status': models.CharField(max_length=255, choices=model_class.MetaState.states.iteritems(), default=model_class.MetaState.default)}

    def status_color(self):
        return self.MetaState.states_colors.get(self.status, 'default')

    def status_icon(self):
        return self.MetaState.states_icons.get(self.status, '')

    def may_switch_to(self, user, dest_state):
        """Return true if we MAY switch to a specific states (not including error, but including rights)"""
        if self.status == dest_state:
            return False

        if user.is_superuser:
            return True

        return dest_state in self.MetaState.states_links[self.status]

    def can_switch_to(self, user, dest_state):
        """Return (IfOk, Message) if someone can switch to a speficic state."""
        return (True, None)

    @property
    def states_links_with_ids(self):
        by_ids = {}

        current_id = 0

        for elem, __ in self.MetaState.states.iteritems():
            by_ids[elem] = current_id
            current_id += 1

        retour_links = []

        for elem, __ in self.MetaState.states.iteritems():
            tmp = []

            for elem_dest in self.MetaState.states_links[elem]:
                tmp.append(by_ids[elem_dest])
            retour_links.append(tmp)

        return retour_links


class GenericLogEntry(models.Model):

    when = models.DateTimeField(auto_now_add=True)
    extra_data = models.TextField(blank=True)
    who = models.ForeignKey(TruffeUser)

    LOG_TYPES = (
        ('created', _(u'Creation')),
        ('edited', _(u'Edité')),
        ('deleted', _(u'Supprimé')),
        ('restored', _(u'Restauré')),
        ('state_changed', _(u'Status changé'))
    )

    what = models.CharField(max_length=64, choices=LOG_TYPES)

    def json_extra_data(self):
        return json.loads(self.extra_data)

    class Meta:
        abstract = True


class GenericStateValidableOrModerable(object):
    """Un système de status générique pour de la modération/validation"""

    moderable_object = True
    moderable_state = '1_asking'

    generic_state_unit_field = '!root'  # !root for the root unit, or the field with an unit
    generic_state_moderable = True  # To use the term 'Moderate' sinon 'Validé'

    def __init__(self, *args, **kwargs):

        super(GenericStateValidableOrModerable, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'VALIDATE': _(u'Peut modérer cet élément'),
        })

    class MetaState_:
        """Full object defined in subclasses !"""

        default = '0_draft'

        states_links = {
            '0_draft': ['1_asking', '3_archive'],
            '1_asking': ['0_draft', '2_online', '3_archive'],
            '2_online': ['0_draft', '3_archive'],
            '3_archive': [],
        }

        states_colors = {
            '0_draft': 'primary',
            '1_asking': 'danger',
            '2_online': 'success',
            '3_archive': 'default',
        }

        states_icons = {
            '0_draft': '',
            '1_asking': '',
            '2_online': '',
            '3_archive': '',
        }

        states_default_filter = '0_draft,1_asking,2_online'
        status_col_id = 3

    def may_switch_to(self, user, dest_state):

        if dest_state == '0_draft' and not super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return False

        if self.rights_can('EDIT', user) or (self.status in ['1_asking', '2_online'] and dest_state != '2_online' and super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)):
            return super(GenericStateValidableOrModerable, self).may_switch_to(user, dest_state)

        return False

    def can_switch_to(self, user, dest_state):

        if self.status == '3_archive' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if dest_state == '2_online' and not self.rights_can('VALIDATE', user):
            return (False, _(u'Seul un modérateur peut valider cet object. Merci de passer cet object en status \'Modération en cours\' pour demander une validation.'))

        if self.status == '2_online' and super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return (True, None)

        if dest_state == '0_draft' and not super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return (False, _(u'Les modérateurs ne peuvent pas repasser en brouillion un object qui ne leur appartiens pas'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits'))

        return super(GenericStateValidableOrModerable, self).can_switch_to(user, dest_state)

    def rights_can_SHOW(self, user):

        if super(GenericStateValidableOrModerable, self).rights_can_SHOW(user):
            return True

        # Si le status est en cours de validation ou validé, les modérateurs peuvent voir
        if self.status in ['1_asking', '2_online']:
            return self.rights_can_VALIDATE(user)

    def rights_can_VALIDATE(self, user):
        if self.status == '3_archive':
            return False

        if self.generic_state_unit_field == '!root':
            return self.rights_in_root_unit(user, self.MetaRightsUnit.moderation_access)
        else:
            return self.rights_in_unit(user, get_property(self, self.generic_state_unit_field), self.MetaRightsUnit.moderation_access)

    def rights_peoples_in_VALIDATE(self, no_parent=False):

        if self.generic_state_unit_field == '!root':
            return self.people_in_root_unit(self.MetaRightsUnit.moderation_access)
        else:
            return self.people_in_unit(get_property(self, self.generic_state_unit_field), self.MetaRightsUnit.moderation_access, no_parent=no_parent)

    def rights_can_EDIT(self, user):

        if self.status == '3_archive':
            return False

        if self.status == '2_online' and not self.rights_can('VALIDATE', user):
            return False

        # Si le status est en cours de validation ou validé, les modérateurs
        # peuvent editer
        if self.status in ['1_asking', '2_online']:
            return self.rights_can_VALIDATE(user)

        return super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)

    def rights_can_DISPLAY_LOG(self, user):
        return super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)

    def rights_can_DELETE(self, user):

        # ! Pas de supression même si on est modérateur
        if self.status == '3_archive':
            return False

        return super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)

    def switch_status_signal(self, request, old_status, dest_status):

        s = super(GenericStateValidableOrModerable, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(old_status, dest_status)

        if dest_status == '1_asking':
            notify_people(request, '%s.moderation' % (self.__class__.__name__,), 'moderation', self, self.build_group_members_for_validators())

        if dest_status == '2_online':
            unotify_people('%s.moderation' % (self.__class__.__name__,), self)

            if self.generic_state_moderable:
                notify_people(request, '%s.online' % (self.__class__.__name__,), 'online', self, self.build_group_members_for_editors())
            else:
                notify_people(request, '%s.validated' % (self.__class__.__name__,), 'validated', self, self.build_group_members_for_editors())


class GenericStateModerable(GenericStateValidableOrModerable):

    generic_state_moderable = True

    class MetaState(GenericStateValidableOrModerable.MetaState_):

        states = {
            '0_draft': _('Brouillon'),
            '1_asking': _(u'Modération en cours'),
            '2_online': _(u'En ligne'),
            '3_archive': _(u'Archivé'),
        }
        default = '0_draft'

        states_texts = {
            '0_draft': _(u'L\'objet est en cours de création et n\'est pas public.'),
            '1_asking': _(u'L\'objet est en cours de modération. Il n\'est pas éditable. Sélectionner ce status pour demander une modération !'),
            '2_online': _(u'L\'objet est publié. Il n\'est pas éditable.'),
            '3_archive': _(u'L\'objet est archivé. Il n\'est plus modifiable.'),
        }

        states_quick_switch = {
            '0_draft': ('1_asking', _(u'Demander à modérer')),
            '1_asking': ('2_online', _(u'Mettre en ligne')),
            '2_online': ('0_draft', _(u'Repasser en brouillon')),
        }


class GenericStateValidable(GenericStateValidableOrModerable):

    generic_state_moderable = False

    class MetaState(GenericStateValidableOrModerable.MetaState_):

        states = {
            '0_draft': _('Brouillon'),
            '1_asking': _(u'Validation en cours'),
            '2_online': _(u'Validé'),
            '3_archive': _(u'Archivé'),
        }
        default = '0_draft'

        states_texts = {
            '0_draft': _(u'La réservation est en cours de création et n\'est pas public.'),
            '1_asking': _(u'La réservation est en cours de modération. Elle n\'est pas éditable. Sélectionner ce status pour demander une modération !'),
            '2_online': _(u'La résevation est validée. Elle n\'est pas éditable.'),
            '3_archive': _(u'La réservation est archivée. Elle n\'est plus modifiable.'),
        }

        states_quick_switch = {
            '0_draft': ('1_asking', _(u'Demander à modérer')),
            '1_asking': ('2_online', _(u'Valider')),
            '2_online': ('0_draft', _(u'Repasser en brouillon')),
        }


class GenericStateRootModerable(GenericStateModerable):
    """Un système de status générique pour de la modération par l'unité racine"""

    generic_state_unit_field = '!root'


class GenericStateUnitValidable(GenericStateValidable):
    """Un système de status générique pour de la validation par une unité. Définir generic_state_unit_field !"""


class GenericGroupsModel():

    class MetaGroups:
        groups = {
            'creator': _(u'Créateur de cet élément'),
            'editors': _(u'Personnes ayant modifié cet élément (y compris le status)'),
            'canedit': _(u'Personnes pouvant éditer cet élément')
        }

        @classmethod
        def groups_update(cls, new_groups):
            cls.groups = copy.deepcopy(cls.groups)
            cls.groups.update(new_groups)

    def build_group_members_for_creator(self):
        return [self.logs.filter(what='created').first().who]

    def build_group_members_for_editors(self):
        retour = []

        for log in self.logs.all():
            if log.who not in retour:
                retour.append(log.who)

        return retour

    def build_group_members_for_canedit(self):
        return self.rights_peoples_in_EDIT()


class GenericGroupsValidableOrModerableModel(object):

    generic_groups_moderable = True

    def __init__(self, *args, **kwargs):

        super(GenericGroupsValidableOrModerableModel, self).__init__(*args, **kwargs)

        self.MetaGroups.groups_update({
            'validators':
                _(u'Personnes pouvant modérer cet élément') if self.generic_groups_moderable else
                _(u'Personnes pouvant valider cet élément'),
        })

    def build_group_members_for_validators(self):
        return self.rights_peoples_in_VALIDATE(no_parent=True)  # Pas besion d'informer les gens avec un droit supérieur :)


class GenericGroupsModerableModel(GenericGroupsValidableOrModerableModel):
    generic_groups_moderable = True


class GenericGroupsValidableModel(GenericGroupsValidableOrModerableModel):
    generic_groups_moderable = False


class GenericContactableModel():

    def contactables_groups(self):
        return self.MetaGroups.groups


class GenericExternalUnitAllowed():
    """Rend l'utilisation d'unités externes possibles"""

    @staticmethod
    def do(module, models_module, model_class, cache):
        """Execute code at startup"""

        return {
            'unit': models.ForeignKey(cache['units.models.Unit'], blank=True, null=True),
            'unit_blank_user': models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True),
            'unit_blank_name': models.CharField(_(u'Nom de l\'entité externe'), max_length=255, blank=True, null=True),
        }


    def get_unit_name(self):

        if self.unit:
            return '<span class="label label-success">%s</span>' % (self.unit,)

        return '<span class="label label-warning">%s (Externe, par %s)</span>' % (self.unit_blank_name, self.unit_blank_user)
