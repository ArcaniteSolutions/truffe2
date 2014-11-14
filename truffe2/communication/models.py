# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, GenericStateModerable, FalseFK
from django.utils.translation import ugettext_lazy as _

from rights.utils import UnitEditableModel


class _WebsiteNews(GenericModel, GenericStateModerable, GenericStateModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'
        moderation_access = 'COMMUNICATION'

    title = models.CharField(max_length=255)
    content = models.TextField()
    url = models.URLField(max_length=255)
    unit = FalseFK('units.models.Unit')

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('status', _('Status')),
        ]
        details_display = list_display + [('content', _('Content')), ('url', _('URL'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _('News AGEPoly')
        list_title = _(u'Liste de toutes les news sur le site de l\'AGEPoly')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-bullhorn'

        menu_id = 'menu-communication-websitenews'

        datetime_fields = ['start_date', 'end_date']

        has_unit = True

        help_list = _(u"""Les news du site de l'AGEPoly sont les nouvelles affichées sur toutes les pages du site de l'AGEPoly.

Elles sont soumises à modération par le responsable communication de l'AGEPoly avant d'être visibles.""")

    class MetaEdit:
        date_time_fields = ('start_date', 'end_date')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _AgepSlide(GenericModel, GenericStateModerable, GenericStateModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'
        moderation_access = 'COMMUNICATION'

    title = models.CharField(max_length=255)
    picture = models.ImageField(upload_to='uploads/slides/')
    unit = FalseFK('units.models.Unit')

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('status', _('Status')),
        ]
        details_display = list_display + [('picture', _('Image'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _(u'Slide à AGEPoly')
        list_title = _(u'Liste de toutes les slides à l\'AGEPoly')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-bullhorn'

        menu_id = 'menu-communication-agepslide'

        datetime_fields = ['start_date', 'end_date']
        images_fields = ['picture', ]

        has_unit = True

        help_list = _(u"""Les slides à l'AGEPoly sont affichés de manière alléatoire sur les écrans à l'AGEPoly.

Ils sont soumis à modération par le responsable communication de l'AGEPoly avant d'être visibles.""")

    class MetaEdit:
        date_time_fields = ('start_date', 'end_date')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title
