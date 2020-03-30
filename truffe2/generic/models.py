# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.forms import CharField, Textarea, Form
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

import json
import copy
import inspect
import importlib
import os
from pytz import timezone
from datetime import timedelta
import mimetypes
from haystack import indexes
import textract
from celery_haystack.indexes import CelerySearchIndex

from users.models import TruffeUser
from generic import views
from generic.forms import GenericForm
from generic.search import SearchableModel
from app.utils import get_property
from notifications.utils import notify_people, unotify_people
from rights.utils import AutoVisibilityLevel


moderable_things = []
copiable_things = []

GENERICS_MODELS = {}  # Dict of id -> (Model, ModelLogging)


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
            if str(e) not in ["No module named urls", "No module named views", "No module named forms", "No module named models"]:
                raise

        try:
            search_indexes_module = importlib.import_module('.search_indexes', app)
        except:
            search_indexes_module = None

        clsmembers = inspect.getmembers(models_module, inspect.isclass)

        # sorted by line numbers instead of names when possible
        linecls = {}
        for cls in clsmembers:
            try:
                linecls[cls[0]] = inspect.getsourcelines(cls[1])[1]
            except:
                linecls[cls[0]] = -1
        clsmembers = sorted(clsmembers, key=lambda cls: linecls[cls[0]])

        for model_name, model_class in clsmembers:
            if issubclass(model_class, Class) and model_class != Class and model_class not in already_returned:

                data = (module, (views_module, urls_module, models_module, forms_module, search_indexes_module), model_class)

                # Special case for unit, who must be loaded first
                if model_name in ['_Unit', '_Role', '_AccountingYear']:
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

        from accounting_core.utils import AccountingYearLinked, CostCenterLinked

        classes = build_models_list_of(GenericModel)

        cache = {}

        for module, (views_module, urls_module, models_module, forms_module, search_indexes_module), model_class in classes:

            if model_class.__name__[0] != '_':
                continue

            # Create the new model
            extra_data = {'__module__': models_module.__name__}

            for SpecificClass in [GenericStateModel, GenericExternalUnitAllowed, GenericDelayValidableInfo, AccountingYearLinked, AutoVisibilityLevel, CostCenterLinked]:
                if issubclass(model_class, SpecificClass):
                    extra_data.update(SpecificClass.do(module, models_module, model_class, cache))

            for key, value in model_class.__dict__.iteritems():
                if hasattr(value, '__class__') and value.__class__ == FalseFK:
                    extra_data.update({key: models.ForeignKey(cache[value.model], *value.args, **value.kwargs)})

            real_model_class = type(model_class.__name__[1:], (model_class,), extra_data)

            setattr(models_module, real_model_class.__name__, real_model_class)
            cache['%s.%s' % (models_module.__name__, real_model_class.__name__)] = real_model_class

            # Add the logging model
            logging_class = type('%sLogging' % (real_model_class.__name__,), (GenericLogEntry,), {'object': models.ForeignKey(real_model_class, related_name='logs'), '__module__': models_module.__name__})
            setattr(models_module, logging_class.__name__, logging_class)

            # Add the view model
            views_class = type('%sViews' % (real_model_class.__name__,), (GenericObjectView,), {'object': models.ForeignKey(real_model_class, related_name='views'), '__module__': models_module.__name__})
            setattr(models_module, views_class.__name__, views_class)
            setattr(real_model_class, "_t2_views_class", views_class)

            unikey = '{}.{}'.format(models_module.__name__, real_model_class.__name__)
            GENERICS_MODELS[unikey] = (real_model_class, logging_class)

            # Add the file model (if needed)
            if issubclass(model_class, GenericModelWithFiles):
                file_class = type('%sFile' % (real_model_class.__name__,), (GenericFile,), {'object': models.ForeignKey(real_model_class, related_name='files', blank=True, null=True), 'file': models.FileField(upload_to='uploads/_generic/%s/' % (real_model_class.__name__,)), '__module__': models_module.__name__})
                setattr(models_module, file_class.__name__, file_class)

                full_upload_path = '%s/uploads/_generic/%s/' % (settings.MEDIA_ROOT, real_model_class.__name__)

                if not os.path.isdir(full_upload_path):
                    print "[!] %s need to be a folder for file uplodad ! (And don\'t forget the gitignore)" % (full_upload_path,)

            else:
                file_class = None

            # Add the tag model (if needed)
            if issubclass(model_class, GenericTaggableObject):
                tag_class = type('%sTag' % (real_model_class.__name__,), (GenericTag,), {'object': models.ForeignKey(real_model_class, related_name='tags'), '__module__': models_module.__name__})
                setattr(models_module, tag_class.__name__, tag_class)
            else:
                tag_class = None

            # Create the form module
            def generate_meta(Model):
                class Meta():
                    model = Model
                    exclude = ('deleted', 'status', 'accounting_year')

                class MetaNoUnit():
                    model = Model
                    exclude = ('deleted', 'status', 'accounting_year', 'unit')

                class MetaNoUnitExternal():
                    model = Model
                    exclude = ('deleted', 'status', 'accounting_year', 'unit', 'unit_blank_user')

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

                setattr(views_module, '%s_list' % (base_views_name,), views.generate_list(module, base_views_name, real_model_class, tag_class))
                setattr(views_module, '%s_list_json' % (base_views_name,), views.generate_list_json(module, base_views_name, real_model_class, tag_class))
                setattr(views_module, '%s_logs' % (base_views_name,), views.generate_logs(module, base_views_name, real_model_class))
                setattr(views_module, '%s_logs_json' % (base_views_name,), views.generate_logs_json(module, base_views_name, real_model_class, logging_class))
                setattr(views_module, '%s_edit' % (base_views_name,), views.generate_edit(module, base_views_name, real_model_class, form_model_class, logging_class, file_class, tag_class))
                setattr(views_module, '%s_show' % (base_views_name,), views.generate_show(module, base_views_name, real_model_class, logging_class, tag_class))
                setattr(views_module, '%s_delete' % (base_views_name,), views.generate_delete(module, base_views_name, real_model_class, logging_class))
                setattr(views_module, '%s_deleted' % (base_views_name,), views.generate_deleted(module, base_views_name, real_model_class, logging_class))
                setattr(views_module, '%s_mayi' % (base_views_name,), views.generate_mayi(module, base_views_name, real_model_class, logging_class))

                # Add urls to views
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%s/$' % (base_views_name,), '%s_list' % (base_views_name,)),
                    url(r'^%s/mayi$' % (base_views_name,), '%s_mayi' % (base_views_name,)),
                    url(r'^%s/json$' % (base_views_name,), '%s_list_json' % (base_views_name,)),
                    url(r'^%s/deleted$' % (base_views_name,), '%s_deleted' % (base_views_name,)),
                    url(r'^%s/logs$' % (base_views_name,), '%s_logs' % (base_views_name,)),
                    url(r'^%s/logs/json$' % (base_views_name,), '%s_logs_json' % (base_views_name,)),
                    url(r'^%s/(?P<pk>[0-9~]+)/edit$' % (base_views_name,), '%s_edit' % (base_views_name,)),
                    url(r'^%s/(?P<pk>[0-9,]+)/delete$' % (base_views_name,), '%s_delete' % (base_views_name,)),
                    url(r'^%s/(?P<pk>[0-9]+)/$' % (base_views_name,), '%s_show' % (base_views_name,)),
                )

                setattr(real_model_class, '_show_view', '%s.%s_show' % (views_module.__name__, base_views_name,))

            if issubclass(model_class, GenericStateModel):
                setattr(views_module, '%s_switch_status' % (base_views_name,), views.generate_switch_status(module, base_views_name, real_model_class, logging_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%s/(?P<pk>[0-9,]+)/switch_status$' % (base_views_name,), '%s_switch_status' % (base_views_name,)),
                )

            if hasattr(model_class.MetaData, 'menu_id_calendar'):
                setattr(views_module, '%s_calendar' % (base_views_name,), views.generate_calendar(module, base_views_name, real_model_class))
                setattr(views_module, '%s_calendar_json' % (base_views_name,), views.generate_calendar_json(module, base_views_name, real_model_class))

                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%s/calendar/$' % (base_views_name,), '%s_calendar' % (base_views_name,)),
                    url(r'^%s/calendar/json$' % (base_views_name,), '%s_calendar_json' % (base_views_name,)),
                )

            if hasattr(model_class.MetaData, 'menu_id_calendar_related'):
                setattr(views_module, '%s_calendar_related' % (base_views_name,), views.generate_calendar_related(module, base_views_name, real_model_class))
                setattr(views_module, '%s_calendar_related_json' % (base_views_name,), views.generate_calendar_related_json(module, base_views_name, real_model_class))

                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%s/related/calendar/$' % (base_views_name,), '%s_calendar_related' % (base_views_name,)),
                    url(r'^%s/related/calendar/json$' % (base_views_name,), '%s_calendar_related_json' % (base_views_name,)),
                )

            if issubclass(model_class, GenericStateUnitValidable):
                setattr(views_module, '%s_list_related' % (base_views_name,), views.generate_list_related(module, base_views_name, real_model_class))
                setattr(views_module, '%s_list_related_json' % (base_views_name,), views.generate_list_related_json(module, base_views_name, real_model_class))
                setattr(views_module, '%s_calendar_specific' % (base_views_name,), views.generate_calendar_specific(module, base_views_name, real_model_class))
                setattr(views_module, '%s_calendar_specific_json' % (base_views_name,), views.generate_calendar_specific_json(module, base_views_name, real_model_class))
                setattr(views_module, '%s_directory' % (base_views_name,), views.generate_directory(module, base_views_name, real_model_class))

                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%s/related/$' % (base_views_name,), '%s_list_related' % (base_views_name,)),
                    url(r'^%s/related/json$' % (base_views_name,), '%s_list_related_json' % (base_views_name,)),

                    url(r'^%s/specific/(?P<pk>[0-9~]+)/calendar/$' % (base_views_name,), '%s_calendar_specific' % (base_views_name,)),
                    url(r'^%s/specific/(?P<pk>[0-9~]+)/calendar/json$' % (base_views_name,), '%s_calendar_specific_json' % (base_views_name,)),
                    url(r'^%s/directory/$' % (base_views_name,), '%s_directory' % (base_views_name,)),
                )

            if issubclass(model_class, GenericStateValidableOrModerable) and real_model_class not in moderable_things:
                moderable_things.append(real_model_class)

            if issubclass(model_class, AccountingYearLinked) and hasattr(model_class, 'MetaAccounting') and hasattr(model_class.MetaAccounting, 'copiable') and model_class.MetaAccounting.copiable and real_model_class not in copiable_things:
                copiable_things.append(real_model_class)

            if issubclass(model_class, GenericContactableModel):
                setattr(views_module, '%s_contact' % (base_views_name,), views.generate_contact(module, base_views_name, real_model_class, logging_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%s/(?P<pk>[0-9]+)/contact/(?P<key>.+)$' % (base_views_name,), '%s_contact' % (base_views_name,)),
                )

            if file_class:
                setattr(views_module, '%s_file_upload' % (base_views_name,), views.generate_file_upload(module, base_views_name, real_model_class, logging_class, file_class))
                setattr(views_module, '%s_file_delete' % (base_views_name,), views.generate_file_delete(module, base_views_name, real_model_class, logging_class, file_class))
                setattr(views_module, '%s_file_get' % (base_views_name,), views.generate_file_get(module, base_views_name, real_model_class, logging_class, file_class))
                setattr(views_module, '%s_file_get_thumbnail' % (base_views_name,), views.generate_file_get_thumbnail(module, base_views_name, real_model_class, logging_class, file_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%sfile/upload$' % (base_views_name,), '%s_file_upload' % (base_views_name,)),
                    url(r'^%sfile/(?P<pk>[0-9]+)/delete$' % (base_views_name,), '%s_file_delete' % (base_views_name,)),
                    url(r'^%sfile/(?P<pk>[0-9]+)/get/.*$' % (base_views_name,), '%s_file_get' % (base_views_name,)),
                    url(r'^%sfile/(?P<pk>[0-9]+)/thumbnail$' % (base_views_name,), '%s_file_get_thumbnail' % (base_views_name,)),
                )

            if tag_class:
                setattr(views_module, '%s_tag_search' % (base_views_name,), views.generate_tag_search(module, base_views_name, real_model_class, logging_class, tag_class))
                urls_module.urlpatterns += patterns(views_module.__name__,
                    url(r'^%stags/search$' % (base_views_name,), '%s_tag_search' % (base_views_name,)),
                )

            if issubclass(model_class, SearchableModel):
                if not search_indexes_module:
                    raise(Exception("{} need a search_indexes.py, please create it in {}/".format(model_class.__name__, module.__name__)))

                index = index_generator(real_model_class)
                setattr(search_indexes_module, index.__name__, index)

    def build_state(self):
        """Return the current state of the object. Used for diffs."""
        retour = {}
        opts = self._meta
        for f in sorted(opts.fields + opts.many_to_many):
            if isinstance(f, models.DateTimeField):
                if not getattr(self, f.name):
                    retour[f.name] = None
                else:
                    loc = getattr(self, f.name).astimezone(timezone(settings.TIME_ZONE))
                    retour[f.name] = loc.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(f, models.ManyToManyField):
                retour[f.name] = u', '.join([unicode(x) for x in getattr(self, f.name).all()])

            else:
                retour[f.name] = unicode(getattr(self, f.name))

        return retour

    def last_log(self):
        """Return the last log entry"""
        return self.logs.order_by('-when').first()

    def get_creator(self):
        """Return the creator (based on logs)"""
        return getattr(self.logs.filter(what='created').first(), 'who', None)

    def get_creation_date(self):
        """Return the creation date (based on logs)"""
        return getattr(self.logs.filter(what='created').first(), 'when', None)

    def display_url(self):
        return reverse(str(self.__class__._show_view), args=(self.pk,))

    class Meta:
        abstract = True

    def get_full_class_name(self):
        return '{}.{}'.format(self.__class__.__module__, self.__class__.__name__)

    def is_new(self, user):
        """Return true is the model has unseen updates for a user"""

        try:
            view_obj = self.views.get(who=user)
            return view_obj.when <= self.last_log().when
        except self._t2_views_class.DoesNotExist:
            return True

    def user_has_seen_object(self, user):

        view_obj, __ = self._t2_views_class.objects.get_or_create(object=self, who=user)
        view_obj.when = now()
        view_obj.save()


class GenericModelWithFiles(object):
    """Un modèle généric auquel on peut uploader des fichiers"""

    def get_images_files(self):
        retour = []

        for file in self.files.all():
            if file.is_picture():
                retour.append(file)

        return retour

    def get_pdf_files(self):
        retour = []

        for file in self.files.all():
            if file.is_pdf():
                retour.append(file)

        return retour


class GenericFile(models.Model):
    """Un fichier uploadé pour un GenericModelWithFiles"""

    # NB: The ForgienKey AND the file field are generated dynamicaly
    upload_date = models.DateTimeField(auto_now_add=True)
    uploader = models.ForeignKey(TruffeUser)

    def basename(self):
        return os.path.basename(self.file.path)

    def is_picture(self):
        type, __ = mimetypes.guess_type(self.file.path)

        return type and type.startswith('image/')

    def is_pdf(self):
        type, __ = mimetypes.guess_type(self.file.path)

        return type == 'application/pdf'

    class Meta:
        abstract = True


class GenericStateModel(object):
    """Un modele generic avec une notion de statut"""

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

    @property
    def states_forced_pos_x(self):
        """Helper for simple template language"""

        retour = {}

        for k, (x, _) in self.MetaState.forced_pos.iteritems():
            retour[k] = x

        return retour

    @property
    def states_forced_pos_y(self):
        """Helper for simple template language"""

        retour = {}

        for k, (_, y) in self.MetaState.forced_pos.iteritems():
            retour[k] = y

        return retour


class GenericLogEntry(models.Model):

    when = models.DateTimeField(auto_now_add=True)
    extra_data = models.TextField(blank=True)
    who = models.ForeignKey(TruffeUser)

    LOG_TYPES = (
        ('imported', _(u'Importé depuis Truffe 1')),
        ('created', _(u'Creation')),
        ('edited', _(u'Edité')),
        ('deleted', _(u'Supprimé')),
        ('restored', _(u'Restauré')),
        ('state_changed', _(u'Statut changé')),
        ('file_added', _(u'Fichier ajouté')),
        ('file_removed', _(u'Fichier supprimé')),
    )

    what = models.CharField(max_length=64, choices=LOG_TYPES)

    def json_extra_data(self):
        return json.loads(self.extra_data)

    class Meta:
        abstract = True


class GenericObjectView(models.Model):

    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(TruffeUser)

    class Meta:
        abstract = True


class GenericStateValidableOrModerable(object):
    """Un système de statut générique pour de la modération/validation"""

    moderable_object = True
    moderable_state = '1_asking'

    def __init__(self, *args, **kwargs):

        super(GenericStateValidableOrModerable, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'VALIDATE': _(u'Peut modérer cet élément'),
        })

    class MetaState_:
        """Full object defined in subclasses !"""

        unit_field = '!root'  # !root for the root unit, or the field with an unit
        moderable = True  # To use the term 'Moderate' sinon 'Validé'

        default = '0_draft'

        states_links = {
            '0_draft': ['1_asking', '3_archive'],
            '1_asking': ['0_draft', '2_online', '3_archive', '4_deny'],
            '2_online': ['0_draft', '3_archive', '4_canceled'],
            '3_archive': [],
            '4_deny': ['1_asking', '3_archive'],
            '4_canceled': ['1_asking', '3_archive'],
        }

        states_colors = {
            '0_draft': 'primary',
            '1_asking': 'warning',
            '2_online': 'success',
            '3_archive': 'default',
            '4_deny': 'danger',
            '4_canceled': 'danger',
        }

        states_icons = {
            '0_draft': '',
            '1_asking': '',
            '2_online': '',
            '3_archive': '',
            '4_deny': '',
            '4_canceled': '',
        }

        list_quick_switch = {
            '0_draft': [('1_asking', 'fa fa-question', _(u'Demander à modérer')), ],
            '1_asking': [('2_online', 'fa fa-check', _(u'Valider')), ('4_deny', 'fa fa-ban', _(u'Refuser'))],
            '2_online': [('3_archive', 'glyphicon glyphicon-remove-circle', _(u'Archiver')), ('4_canceled', 'fa fa-ban', _(u'Annuler'))],
            '3_archive': [],
            '4_deny': [],
            '4_canceled': [],
        }

        forced_pos = {
            '0_draft': (0.1, 0.15),
            '1_asking': (0.5, 0.15),
            '2_online': (0.9, 0.85),
            '3_archive': (0.9, 0.5),
            '4_deny': (0.9, 0.15),
            '4_canceled': (0.5, 0.85),
        }

        states_default_filter = '0_draft,1_asking,2_online'
        states_default_filter_related = '1_asking,2_online'
        status_col_id = 4

    def may_switch_to(self, user, dest_state):

        if dest_state == '0_draft' and not super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return False

        if self.rights_can('EDIT', user) or (self.status in ['1_asking', '2_online'] and dest_state not in ['2_online', '4_deny'] and super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)):
            return super(GenericStateValidableOrModerable, self).may_switch_to(user, dest_state)

        return False

    def can_switch_to(self, user, dest_state):

        if self.status == '3_archive' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if dest_state == '2_online' and not self.rights_can('VALIDATE', user):
            return (False, _(u'Seul un modérateur peut valider cet élément. Merci de passer cet élément dans le statut \'Modération en cours\' pour demander une validation.'))

        if dest_state == '4_deny' and not self.rights_can('VALIDATE', user):
            return (False, _(u'Seul un modérateur peut refuser cet élément.'))

        if self.status == '2_online' and super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return (True, None)

        if dest_state == '0_draft' and not super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return (False, _(u'Les modérateurs ne peuvent pas repasser en brouillon un élément qui ne leur appartient pas.'))

        if dest_state == '0_draft' and self.status == '1_asking' and super(GenericStateValidableOrModerable, self).rights_can_EDIT(user):
            return (True, None)

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

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

        if self.MetaState.unit_field == '!root':
            return self.rights_in_root_unit(user, self.MetaRightsUnit.moderation_access)
        else:
            return self.rights_in_unit(user, get_property(self, self.MetaState.unit_field), self.MetaRightsUnit.moderation_access)

    def rights_peoples_in_VALIDATE(self, no_parent=False):

        if self.MetaState.unit_field == '!root':
            return self.people_in_root_unit(self.MetaRightsUnit.moderation_access)
        else:
            return self.people_in_unit(get_property(self, self.MetaState.unit_field), self.MetaRightsUnit.moderation_access, no_parent=no_parent)

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
        return self.rights_can('VALIDATE', user) or super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)

    def rights_can_DELETE(self, user):

        # ! Pas de suppression même si on est modérateur
        if self.status == '3_archive':
            return False

        return super(GenericStateValidableOrModerable, self).rights_can_EDIT(user)

    def switch_status_signal(self, request, old_status, dest_status):

        s = super(GenericStateValidableOrModerable, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

        if dest_status == '1_asking':
            notify_people(request, '%s.moderation' % (self.__class__.__name__,), 'moderation', self, self.build_group_members_for_validators())

        if dest_status == '4_deny':
            unotify_people('%s.moderation' % (self.__class__.__name__,), self)
            notify_people(request, '%s.refused' % (self.__class__.__name__,), 'refused', self, self.build_group_members_for_editors())

        if dest_status == '2_online':
            unotify_people('%s.moderation' % (self.__class__.__name__,), self)

            if self.MetaState.moderable:
                notify_people(request, '%s.online' % (self.__class__.__name__,), 'online', self, self.build_group_members_for_editors())
            else:
                notify_people(request, '%s.validated' % (self.__class__.__name__,), 'validated', self, self.build_group_members_for_editors())

        if old_status == '2_online' and dest_status == '0_draft':
            notify_people(request, '%s.drafted' % (self.__class__.__name__,), 'drafted', self, self.build_group_members_for_validators())

        if dest_status == '4_canceled':
            notify_people(request, '%s.canceled' % (self.__class__.__name__,), 'canceled', self, self.build_group_members_for_cancel())

    def build_group_members_for_cancel(self):
        people = self.build_group_members_for_validators()

        for user in self.build_group_members_for_editors():
            if user not in people:
                people.append(user)

        return people

    def delete_signal(self, request):

        if hasattr(super(GenericStateValidableOrModerable, self), 'delete_signal'):
            super(GenericStateValidableOrModerable, self).delete_signal(request)

        if self.status == '2_online':
            notify_people(request, '%s.deleted' % (self.__class__.__name__,), 'deleted', self, self.build_group_members_for_cancel())


class GenericStateModerable(GenericStateValidableOrModerable):

    class MetaState(GenericStateValidableOrModerable.MetaState_):

        moderable = True

        states = {
            '0_draft': _('Brouillon'),
            '1_asking': _(u'Modération en cours'),
            '2_online': _(u'En ligne'),
            '3_archive': _(u'Archivé'),
            '4_deny': _(u'Refusé'),
            '4_canceled': _(u'Annulé'),
        }
        default = '0_draft'

        states_texts = {
            '0_draft': _(u'L\'objet est en cours de création et n\'est pas public.'),
            '1_asking': _(u'L\'objet est en cours de modération. Il n\'est pas éditable. Sélectionner ce statut pour demander une modération !'),
            '2_online': _(u'L\'objet est publié. Il n\'est pas éditable.'),
            '3_archive': _(u'L\'objet est archivé. Il n\'est plus modifiable.'),
            '4_deny': _(u'L\'objet a été refusé.'),
            '4_canceled': _(u'L\'objet a été annulé.'),
        }

        states_quick_switch = {
            '0_draft': [('1_asking', _(u'Demander à modérer')), ],
            '1_asking': [('2_online', _(u'Mettre en ligne')), ],
            '2_online': [('0_draft', _(u'Repasser en brouillon')), ('3_archive', _(u'Archiver')), ('4_canceled', _(u'Annuler')), ],
        }


class GenericStateValidable(GenericStateValidableOrModerable):

    class MetaState(GenericStateValidableOrModerable.MetaState_):

        moderable = False

        states = {
            '0_draft': _('Brouillon'),
            '1_asking': _(u'Validation en cours'),
            '2_online': _(u'Validé'),
            '3_archive': _(u'Archivé'),
            '4_deny': _(u'Refusé'),
            '4_canceled': _(u'Annulé'),
        }
        default = '0_draft'

        states_texts = {
            '0_draft': _(u'La réservation est en cours de création et n\'est pas publique.'),
            '1_asking': _(u'La réservation est en cours de modération. Elle n\'est pas éditable. Sélectionner ce statut pour demander une modération ! ATTENTION ! Tu acceptes par défaut les conditions de réservation liées !'),
            '2_online': _(u'La résevation est validée. Elle n\'est pas éditable.'),
            '3_archive': _(u'La réservation est archivée. Elle n\'est plus modifiable.'),
            '4_deny': _(u'La modération a été refusée. L\'objet n\'était probablement pas disponible suite à un conflit.'),
            '4_canceled': _(u'La réservation a été annulée.'),
        }

        states_quick_switch = {
            '0_draft': [('1_asking', _(u'Demander à valider')), ],
            '1_asking': [('2_online', _(u'Valider')), ],
            '2_online': [('0_draft', _(u'Repasser en brouillon')), ('3_archive', _(u'Archiver')), ('4_canceled', _(u'Annuler')), ],
        }

        status_col_id = 6

        class FormRemark(Form):
            remark = CharField(label=_('Remarque'), widget=Textarea, required=False)

        states_bonus_form = {
            '0_draft': FormRemark,
            '2_online': FormRemark,
            '4_deny': FormRemark
        }

    def switch_status_signal(self, request, old_status, dest_status):

        s = super(GenericStateValidable, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

        if dest_status == '0_draft' or dest_status == '2_online' or dest_status == '4_deny':

            if request.POST.get('remark'):
                if self.remarks:
                    self.remarks += '\n' + request.POST.get('remark')
                else:
                    self.remarks = request.POST.get('remark')
                self.save()


class GenericAccountingStateModel(object):
    """Un système de statut générique pour les pièces comptables"""

    class MetaState:
        states = {
            '0_draft': _('Brouillon'),
            '0_correct': _(u'Corrections nécessaires'),
            '1_unit_validable': _(u'Attente accord unité'),
            '2_agep_validable': _(u'Attente vérification secrétariat'),
            '3_agep_sig1': _(u'Attente signature CdD 1'),
            '3_agep_sig2': _(u'Attente signature CdD 2'),
            '4_accountable': _(u'A comptabiliser'),
            '5_in_accounting': _(u'En comptabilisation'),
            '6_archived': _(u'Archivé'),
            '6_canceled': _(u'Annulé'),
        }
        default = '0_draft'

        states_texts = {
            '0_draft': _(u'L\'objet est en cours de création.'),
            '0_correct': _(u'L\'objet nécessite d\'être modifié avant d\'être revalidé.'),
            '1_unit_validable': _(u'L\'objet doit être accepté au sein de l\'unité. A partir de maintenant, il n\'est plus éditable.'),
            '2_agep_validable': _(u'L\'objet doit être vérifié par le secrétariat de l\'AGEPoly.'),
            '3_agep_sig1': _(u'L\'objet doit etre validé par un membre du CdD avec droit de signature.'),
            '3_agep_sig2': _(u'L\'objet doit etre validé par un autre membre du CdD avec droit de signature.'),
            '4_accountable': _(u'L\'objet est en attente d\'être comptabilisé.'),
            '5_in_accounting': _(u'L\'objet est en cours de comptabilisation'),
            '6_archived': _(u'L\'objet est comptabilisé et archivé. Il n\'est plus modifiable.'),
            '6_canceled':  _(u'L\'objet a été annulé.'),

        
        }

        states_links = {
            '0_draft': ['1_unit_validable', '6_canceled'],
            '0_correct': ['1_unit_validable', '6_canceled'],
            '1_unit_validable': ['0_correct', '2_agep_validable', '6_canceled'],
            '2_agep_validable': ['0_correct', '3_agep_sig1', '6_canceled'],
            '3_agep_sig1': ['0_correct', '3_agep_sig2', '6_canceled'],
            '3_agep_sig2': ['0_correct', '4_accountable', '6_canceled'],
            '4_accountable': ['5_in_accounting'],
            '5_in_accounting': ['0_correct', '6_archived', '6_canceled'],
            '6_archived': [],
            '6_canceled': [],
        }

        list_quick_switch = {
            '0_draft': [('1_unit_validable', 'fa fa-question', _(u'Demander accord unité'))],
            '0_correct': [('1_unit_validable', 'fa fa-question', _(u'Demander accord unité'))],
            '1_unit_validable': [('2_agep_validable', 'fa fa-question', _(u'Demander accord AGEPoly'))],
            '2_agep_validable': [('3_agep_sig1', 'fa fa-check', _(u'Passer en signature'))],
            '3_agep_sig1': [('3_agep_sig2', 'fa fa-check', _(u'Signer (1)'))],
            '3_agep_sig2': [('4_accountable', 'fa fa-check', _(u'Signer (2)'))],
            '4_accountable':  [('3_accountable', 'fa fa-check', _(u'Marquer comme en comptabilisation'))],
            '5_in_accounting':  [('6_archived', 'glyphicon glyphicon-remove-circle', _(u'Archiver'))],
        }

        states_quick_switch = {
            '0_draft': [('1_unit_validable', _(u'Demander accord unité'))],
            '0_correct': [('1_unit_validable', _(u'Demander accord unité'))],
            '1_unit_validable': [('2_agep_validable', _(u'Demander accord AGEPoly')), ('0_correct', _(u'Demander des corrections'))],
            '2_agep_validable': [('3_agep_sig1', _(u'Demander à signer')), ('0_correct', _(u'Demander des corrections')), ],
            '3_agep_sig1': [('3_agep_sig2',  _(u'Signer (1)')), ('0_correct', _(u'Demander des corrections'))],
            '3_agep_sig2': [('4_accountable', _(u'Signer (2)')), ('0_correct', _(u'Demander des corrections'))]
            '4_accountable': [('5_in_accounting', _(u'Marquer comme en comptabilisation'))]
            '5_in_accounting': [('6_archived', _(u'Archiver'))]
        }

        states_colors = {
            '0_draft': 'primary',
            '0_correct': 'warning',
            '1_unit_validable': 'default',
            '2_agep_validable': 'default',
            '3_agep_sig1': 'default',
            '3_agep_sig2': 'default',
            '4_accountable': 'warning',
            '5_in_accounting': 'info',
            '6_archived': 'success',
            '6_canceled': 'danger',
        }

        states_icons = {
            '0_draft': '',
            '0_correct': '',
            '1_unit_validable': '',
            '2_agep_validable': '',
            '3_agep_sig1': '',
            '3_agep_sig2': '',
            '4_accountable': '',
            '5_in_accounting': '',
            '6_archived': 'fa fa-check',
            '6_canceled': 'fa fa-cross',
        }

        states_default_filter = '0_draft,0_correct,1_unit_validable,2_agep_validable,3_agep_sig1,3_agep_sig2,5_in_accounting'
        status_col_id = 4

        forced_pos = {
            '0_draft': (0.1, 0.15),
            '0_correct': (0.5, 0.85),
            '1_unit_validable': (0.2, 0.40),
            '2_agep_validable': (0.35, 0.40),
            '3_agep_sig1': (0.35, 0.15),
            '3_agep_sig2': (0.5, 0.15),
            '4_accountable': (0.5, 0.40),
            '5_in_accounting': (0.7, 0.40),
            '6_archived': (0.9, 0.40),
            '6_canceled': (0.9, 0.85),
        }

    def may_switch_to(self, user, dest_state):
        if self.status[0] == '4' and not user.is_superuser:
            return False

        if dest_state == '4_canceled' and self.rights_can('EDIT', user):
            return True

        if self.status[0] in ['2', '3'] and not self.rights_in_root_unit(user, ['SECRETARIAT', 'TRESORERIE']) and not user.is_superuser:
            return False

        return super(GenericAccountingStateModel, self).may_switch_to(user, dest_state)

    def can_switch_to(self, user, dest_state):

        if self.status[0] == '4' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé/annulé'))

        if dest_state == '4_canceled' and self.rights_can('EDIT', user):
            return (True, None)

        if self.status[0] in ['2', '3'] and not self.rights_in_root_unit(user, ['SECRETARIAT', 'TRESORERIE']) and not user.is_superuser:
            return (False, _(u'Seul l\'admin peut valider cet élément pour le moment. Merci de patienter.'))

        if self.status[0] == '1' and not self.rights_in_linked_unit(user, 'TRESORERIE') and not self.rights_in_root_unit(user, ['SECRETARIAT', 'TRESORERIE']) and not user.is_superuser:
            return (False, _(u'Seul ton trésorier peut valider cet élément pour le moment.'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

        return super(GenericAccountingStateModel, self).can_switch_to(user, dest_state)

    def rights_can_SHOW(self, user):
        if self.get_creator() == user or (hasattr(self.MetaEdit, 'set_linked_info') and self.MetaEdit.set_linked_info and self.linked_info() and self.linked_info().user_pk == user.pk):
            return True

        return super(GenericAccountingStateModel, self).rights_can_SHOW(user)

    def rights_can_EDIT(self, user):

        if self.status[0] == '4':
            return False

        if self.status[0] in ['2', '3'] and not self.rights_in_root_unit(user, 'TRESORERIE'):
            return False

        if self.status[0] in ['0', '1'] and not self.rights_in_linked_unit(user, 'TRESORERIE'):
            return False

        return super(GenericAccountingStateModel, self).rights_can_EDIT(user)

    def rights_can_DISPLAY_LOG(self, user):

        # Don't disable logs if archived
        return super(GenericAccountingStateModel, self).rights_can_EDIT(user)

    def rights_can_DELETE(self, user):
        if self.status == '4_archived':
            return False

        return super(GenericAccountingStateModel, self).rights_can_EDIT(user)

    def switch_status_signal(self, request, old_status, dest_status):
        s = super(GenericAccountingStateModel, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

        if dest_status == '1_unit_validable':
            notify_people(request, '%s.unit_validable' % (self.__class__.__name__,), 'accounting_validable', self, self.people_in_linked_unit('TRESORERIE'))

        elif dest_status == '2_agep_validable':
            unotify_people('%s.validable' % (self.__class__.__name__,), self)
            notify_people(request, '%s.agep_validable' % (self.__class__.__name__,), 'accounting_validable', self, self.people_in_root_unit(['TRESORERIE', 'SECRETARIAT']))

        elif dest_status == '3_accountable':
            unotify_people('%s.validable' % (self.__class__.__name__,), self)
            notify_people(request, '%s.accountable' % (self.__class__.__name__,), 'accounting_accountable', self, self.people_in_root_unit('SECRETARIAT'))

        elif dest_status == '4_archived':
            if request.POST.get('archive_proving_obj') and self.proving_object:
                self.proving_object.status = '4_archived'
                self.proving_object.save()

            unotify_people('%s.accountable' % (self.__class__.__name__,), self)
            notify_people(request, '%s.accepted' % (self.__class__.__name__,), 'accounting_accepted', self, self.build_group_members_for_canedit())

        elif dest_status == '4_canceled' and self.status != '0_draft':
            notify_people(request, '%s.canceled' % (self.__class__.__name__,), 'accounting_canceled', self, self.build_group_members_for_canedit())


class GenericStateRootModerable(GenericStateModerable):
    """Un système de status générique pour de la modération par l'unité racine"""
    pass


class GenericStateRootValidable(GenericStateValidable):
    """Un système de status générique pour de la modération par l'unité racine"""
    pass


class GenericStateUnitValidable(GenericStateValidable):
    """Un système de status générique pour de la validation par une unité. Définir MetaStateUnit.unit_field et MetaStateUnit.linked_model !"""

    def generic_set_dummy_unit(self, unit):
        x = self.__class__.get_linked_object_class()(**{self.MetaState.unit_field.split('.')[-1]: unit})
        setattr(self, self.MetaState.unit_field.split('.')[0], x)

    @classmethod
    def get_linked_object_class(cls):

        module = importlib.import_module('.'.join(cls.MetaState.linked_model.split('.')[:-1]))

        return getattr(module, cls.MetaState.linked_model.split('.')[-1])

    def get_linked_object(self):
        return getattr(self, self.MetaState.unit_field.split('.')[0])


class GenericGroupsModel():

    class MetaGroups(object):
        groups = {
            'creator': _(u'Créateur de cet élément'),
            'editors': _(u'Personnes ayant modifié cet élément (y compris le statut)'),
            'canedit': _(u'Personnes pouvant éditer cet élément')
        }

        @classmethod
        def groups_update(cls, new_groups):
            cls.groups = copy.deepcopy(cls.groups)
            cls.groups.update(new_groups)

    def build_group_members_for_creator(self):
        return [self.get_creator()]

    def build_group_members_for_editors(self):
        retour = []

        for log in self.logs.all():
            if log.who not in retour:
                retour.append(log.who)

        if hasattr(self, 'responsible') and self.responsible:
            retour.append(self.responsible)

        if hasattr(self, 'user') and self.user:
            retour.append(self.user)

        return retour

    def build_group_members_for_canedit(self):
        return self.rights_peoples_in_EDIT()


class GenericGroupsValidableOrModerableModel(object):

    generic_groups_moderable = True

    class MetaGroups(GenericGroupsModel.MetaGroups):
        pass

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
            return u'<span class="label label-success label-crlf" rel="tooltip"  data-placement="left" title="Créateur: %s">%s</span>' % (self.get_creator(), self.unit,)

        return u'<span class="label label-warning label-crlf">%s (Externe, par %s)</span>' % (self.unit_blank_name, self.unit_blank_user)


class GenericDelayValidableInfo():

    @staticmethod
    def do(module, models_module, model_class, cache):
        """Execute code at startup"""

        return {
            'max_days': models.PositiveIntegerField(_(u'Nombre maximum de jours de réservation'), help_text=_(u'Si supérieur à zéro, empêche de demander une réservation si la longeur de la réservation dure plus longtemps que le nombre de jours défini.'), default=0),
            'max_days_externals': models.PositiveIntegerField(_(u'Nombre maximum de jours de réservation (externes)'), help_text=_(u'Si supérieur à zéro, empêche de demander une réservation si la longeur de la réservation dure plus longtemps que le nombre de jours défini, pour les unités externes.'), default=0),

            'minimum_days_before': models.PositiveIntegerField(_(u'Nombre de jours minimum avant réservation'), help_text=_(u'Si supérieur à zéro, empêche de demander une réservation si la réservation n\'est pas au moins dans X jours.'), default=0),
            'minimum_days_before_externals': models.PositiveIntegerField(_(u'Nombre de jours minimum avant réservation (externes)'), help_text=_(u'Si supérieur à zéro, empêche de demander une réservation si la réservation n\'est pas au plus dans X jours, pour les externes.'), default=0),

            'maximum_days_before': models.PositiveIntegerField(_(u'Nombre de jours maximum avant réservation'), help_text=_(u'Si supérieur à zéro, empêche de demander une réservation si la réservation est dans plus de X jours.'), default=0),
            'maximum_days_before_externals': models.PositiveIntegerField(_(u'Nombre de jours maximum avant réservation (externes)'), help_text=_(u'Si supérieur à zéro, empêche de demander une réservation si la réservation est dans plus de X jours, pour les externes.'), default=0),
        }


class GenericDelayValidable(object):

    def can_switch_to(self, user, dest_state):

        if dest_state == '1_asking' and not self.rights_can('VALIDATE', user):

            nb_days = (self.end_date - self.start_date).days
            in_days = (self.start_date - now()).days

            los = self.get_linked_object()

            if not isinstance(los, list):
                los = [los]

            for lo in los:

                max_days = lo.max_days if self.unit else lo.max_days_externals
                min_in_days = lo.minimum_days_before if self.unit else lo.minimum_days_before_externals
                max_in_days = lo.maximum_days_before if self.unit else lo.maximum_days_before_externals

                if max_days > 0 and nb_days > max_days:
                    return (False, _(u'La résevation pour {} est trop longue ! Maximium {} jours !'.format(lo, max_days)))

                if min_in_days > 0 and in_days < min_in_days:
                    return (False, _(u'La résevation pour {} est trop proche d\'aujourd\'hui ! Minimum {} jours ({}) !'.format(lo, min_in_days, now() + timedelta(days=min_in_days))))

                if max_in_days > 0 and in_days > max_in_days:
                    return (False, _(u'La résevation pour {} est trop loin d\'aujourd\'hui ! Maximum {} jours ({}) !'.format(lo, max_in_days, now() + timedelta(days=max_in_days))))

        return super(GenericDelayValidable, self).can_switch_to(user, dest_state)


class GenericModelWithLines(object):

    class MetaLines():
        lines_objects = [
            # {'title': '', 'class': '', 'form': '', 'related_name': '',
            # 'field': '', 'sortable': False, 'show_list': [('field', 'label'),
            # ]},
        ]


class ModelUsedAsLine(models.Model):
    order = models.SmallIntegerField(default=0)

    class Meta:
        abstract = True


class GenericTaggableObject(object):
    """Un object taggable. Prend en compte l'année comptable et l'unité si présent pour la découverte de tag"""
    pass


class GenericTag(models.Model):

    tag = models.CharField(max_length=255)

    class Meta:
        abstract = True


class LinkedInfoModel(object):

    def __init__(self, *args, **kwargs):

        super(LinkedInfoModel, self).__init__(*args, **kwargs)

        if hasattr(self, 'MetaEdit'):
            self.MetaEdit.set_linked_info = True

    def linked_info(self):
        from accounting_tools.models import LinkedInfo

        object_ct = ContentType.objects.get(app_label=self._meta.app_label, model=self._meta.model_name)
        return LinkedInfo.objects.filter(content_type=object_ct, object_id=self.pk).first()

    def get_fullname(self):
        infos = self.linked_info()

        if infos:
            return u"{} {}".format(infos.first_name, infos.last_name)

        return u""


def index_generator(model_class):

    class _Index(CelerySearchIndex, indexes.Indexable):
        text = indexes.CharField(document=True)
        last_edit_date = indexes.DateTimeField()

        def get_model(self):
            return model_class

        def index_queryset(self, using=None):
            if hasattr(self.get_model(), 'deleted'):
                return self.get_model().objects.filter(deleted=False)
            else:
                return self.get_model().objects

        def prepare_last_edit_date(self, obj):
            try:
                return obj.last_log().when
            except:
                if hasattr(obj.MetaSearch, 'last_edit_date_field'):
                    return get_property(obj, obj.MetaSearch.last_edit_date_field)
                return now()

        def prepare_text(self, obj):

            text = u""

            text += u"{}\n".format(obj.MetaData.base_title)

            if hasattr(obj, 'unit') and obj.unit:
                text += u"{}\n".format(obj.unit)

            if hasattr(obj, 'costcenter') and obj.costcenter:
                text += u"{} {}\n".format(obj.costcenter, obj.costcenter.unit)

            for field in obj.MetaSearch.fields:
                attr = get_property(obj, field)
                if attr:

                    if hasattr(attr, '__call__'):
                        attr = attr()

                    try:
                        text += u"{}\n".format(attr)
                    except Exception:
                        pass

            if obj.MetaSearch.extra_text:
                text += u"{}\n".format(obj.MetaSearch.extra_text)

            if obj.MetaSearch.extra_text_generator:
                text += u"{}\n".format(obj.MetaSearch.extra_text_generator(obj))

            if obj.MetaSearch.index_files:
                for f in obj.files.all():

                    try:
                        txt = textract.process(
                            os.path.join(settings.MEDIA_ROOT, f.file.name),
                            language='fra',
                        ).decode('utf-8')
                    except Exception:
                        txt = u''

                    text += u"{} {}\n".format(f.file.name.split('/')[-1], txt)

            if obj.MetaSearch.linked_lines:
                for key, fields in obj.MetaSearch.linked_lines.iteritems():
                    for line_elem in getattr(obj, key).all():

                        for field in fields:
                            attr = get_property(line_elem, field)

                            if attr:
                                if hasattr(attr, '__call__'):
                                    attr = attr()
                                text += u"{}\n".format(attr)

            if hasattr(obj, 'get_status_display'):
                text += u"{}\n".format(obj.get_status_display())

            return text

    index_class = type('{}Index'.format(model_class.__name__), (_Index,), {})
    return index_class
