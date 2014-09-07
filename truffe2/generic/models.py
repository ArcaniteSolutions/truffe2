# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
import inspect
from users.models import TruffeUser
from django.utils.translation import ugettext_lazy as _
import importlib
from django.conf.urls import patterns, url
from generic import views
from generic.forms import GenericForm
import json
from pytz import timezone


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
                extra_data.update(GenericStateModel.do(module, models_module, model_class))

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

                if hasattr(model_class.MetaData, 'has_unit') and model_class.MetaData.has_unit:
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

                # Add urls to views
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^' + base_views_name + '/$', base_views_name + '_list'),
                    url(r'^' + base_views_name + '/json$', base_views_name + '_list_json'),
                    url(r'^' + base_views_name + '/deleted$', base_views_name + '_deleted'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9~]+)/edit$', base_views_name + '_edit'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/delete$', base_views_name + '_delete'),
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/$', base_views_name + '_show'),
                )

            if issubclass(model_class, GenericStateModel):
                setattr(views_module, base_views_name + '_switch_status', views.generate_switch_status(module, base_views_name, real_model_class, logging_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^' + base_views_name + '/(?P<pk>[0-9]+)/switch_status$', base_views_name + '_switch_status'),
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
                retour[f.name] = str(getattr(self, f.name))

        return retour

    def last_log(self):
        """Return the last log entry"""
        return self.logs.order_by('-when')[0]

    class Meta:
        abstract = True


class GenericStateModel():
    """Un modele generic avec une notiion de status"""

    @staticmethod
    def do(module, models_module, model_class):
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


class GenericStateModerable(object):
    """Un système de status générique pour de la modération"""

    def __init__(self, *args, **kwargs):

        super(GenericStateModerable, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'VALIDATE': _(u'Peut modérer cet élément'),
        })

    class MetaState:
        states = {
            '0_draft': _('Brouillon'),
            '1_asking': _(u'Modération en cours'),
            '2_online': _(u'Validé/En ligne'),
            '3_archive': _(u'Archivé'),
        }
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

        states_texts = {
            '0_draft': _(u'L\'objet est en cours de création et n\'est pas public.'),
            '1_asking': _(u'L\'objet est en cours de modération. Il n\'est pas éditable. Sélectionner ce status pour demander une modération !'),
            '2_online': _(u'L\'objet est validé/publié. Il n\'est pas éditable.'),
            '3_archive': _(u'L\'objet est archivé. Il n\'est plus modifiable.'),
        }

        states_quick_switch = {
            '0_draft': ('1_asking', _(u'Demander à modérer')),
            '1_asking': ('2_online', _(u'Valider')),
            '2_online': ('0_draft', _(u'Repasser en brouillon')),
        }

        states_default_filter = '0_draft,1_asking,2_online'
        status_col_id = 3

    def may_switch_to(self, user, dest_state):
        if self.rights_can('EDIT', user) or (self.status == '2_online' and super(GenericStateModerable, self).rights_can_EDIT(user)):
            return super(GenericStateModerable, self).may_switch_to(user, dest_state)
        return False

    def can_switch_to(self, user, dest_state):

        if self.status == '3_archive' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if dest_state == '2_online' and not self.rights_can('VALIDATE', user):
            return (False, _(u'Seul un modérateur peut valider cet object. Merci de passer cet object en status \'Modération en cours\' pour demander une validation.'))

        if self.status == '2_online' and super(GenericStateModerable, self).rights_can_EDIT(user):
            return (True, None)

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits'))

        return super(GenericStateModerable, self).can_switch_to(user, dest_state)

    def rights_can_VALIDATE(self, user):
        if self.status == '3_archive':
            return False

        return self.rights_in_root_unit(user, self.MetaRightsUnit.moderation_access)

    def rights_can_EDIT(self, user):

        if self.status == '3_archive':
            return False

        if self.status == '2_online' and not self.rights_can('VALIDATE', user):
            return False

        return super(GenericStateModerable, self).rights_can_EDIT(user)
