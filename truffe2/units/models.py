# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel
from django.utils.translation import ugettext_lazy as _


class _Unit(GenericModel):

    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=64, blank=True, null=True, help_text=_(u'Utilisé pour la syncronisation des accréditations'))
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    is_commission = models.BooleanField(default=False, help_text=_(u'Cocher si cette unité est une commission de l\'AGEPoly'))
    is_equipe = models.BooleanField(default=False, help_text=_(u'Cocher si cette unité est une équipe de l\'AGEPoly'))

    parent_herachique = models.ForeignKey('Unit', blank=True, null=True, help_text=_(u'Pour les commission, sélectionner le comité de l\'AGEPoly. Pour les sous-commisions, sélectionner la commission parente. Pour un sous-coaching, sélectionner la commission coaching. Pour le comité de l\'AGEPoly, ne rien mettre.'))

    class MetaData:
        list_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_herachique', _('Parent'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_herachique', _('Parent'))
        ]

        filter_fields = ('name', )

        base_title = _(u'Unités')
        list_title = _(u'Liste de toutes les unités')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name
