# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel
from django.utils.translation import ugettext_lazy as _

from rights.utils import AgepolyEditableModel


class _HomePageNews(GenericModel, GenericStateModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'COMMUNICATION'
        world_ro_access = False

    title = models.CharField(max_length=255)
    content = models.TextField()

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('get_status_display', _('Status')),
        ]
        details_display = list_display + [('content', _('Content'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _('News truffe')
        list_title = _(u'Liste de toutes les news truffe')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-bullhorn'

        menu_id = 'menu-communication-homepagenews'

    class MetaEdit:
        date_time_fields = ('start_date', 'end_date')

    class MetaState:
        states = {
            'draft': _('Brouillon'),
            'moderate': _(u'Modération demandée'),
            'online': _(u'En ligne'),
            'archive': _(u'Archivé'),
            'refuse': _(u'Refusé'),
        }
        default = 'draft'

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title
