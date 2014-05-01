# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel
from django.utils.translation import ugettext_lazy as _


class _HomePageNews(GenericModel, GenericStateModel):

    title = models.CharField(max_length=255)
    content = models.TextField()

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class MetaData:
        list_display = ('title', 'content', 'get_status_display')

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
