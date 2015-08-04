# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


from generic.models import GenericModel, GenericStateModel, FalseFK, GenericGroupsModel
from rights.utils import AgepolyEditableModel


class _Provider(GenericModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255)
    description = models.TextField(_('Description'))

    class MetaData:
        list_display = [
            ('name', _(u'Nom')),
        ]
        details_display = list_display + [
            ('description', _(u'Description')),
        ]

        default_sort = "[1, 'asc']"  # name

        filter_fields = ('name', 'description')

        base_title = _(u'Fournisseurs')
        list_title = _(u'Liste des fournisseurs')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-suitcase'

        menu_id = 'menu-vehicles-provider'

        help_list = _(u"""Les entreprises fournissant des services de locations de véhicules.""")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class _VehicleType(GenericModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = True

    provider = FalseFK('vehicles.models.Provider', verbose_name=_('Fournisseur'))
    name = models.CharField(_('Nom'), max_length=255)
    description = models.TextField(_('Description'))

    class MetaData:
        list_display = [
            ('provider', _(u'Fournisseur')),
            ('name', _(u'Nom')),
        ]
        details_display = list_display + [
            ('description', _(u'Description')),
        ]

        default_sort = "[2, 'asc']"  # name

        filter_fields = ('name', 'description', 'provider__name')

        base_title = _(u'Type de véhicule')
        list_title = _(u'Liste des types de véhicules')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-truck'

        menu_id = 'menu-vehicles-type'

        help_list = _(u"""Les différents types de véhicules, par fournisseur""")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class _Card(GenericModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = False

    provider = FalseFK('vehicles.models.Provider', verbose_name=_('Fournisseur'))
    name = models.CharField(_('Nom'), max_length=255)
    number = models.CharField(_(u'Numéro'), max_length=255)
    description = models.TextField(_('Description'))

    class MetaData:
        list_display = [
            ('provider', _(u'Fournisseur')),
            ('name', _(u'Nom')),
            ('number', _(u'Numéro')),
        ]
        details_display = list_display + [
            ('description', _(u'Description')),
        ]

        default_sort = "[2, 'asc']"  # name

        filter_fields = ('name', 'number', 'description', 'provider__name')

        base_title = _(u'Carte')
        list_title = _(u'Liste des cartes')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-credit-card'

        menu_id = 'menu-vehicles-cards'

        help_list = _(u"""Les différentes cartes utilisées pour les réservations""")

    class Meta:
        abstract = True

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.number)


class _Location(GenericModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255)
    description = models.TextField(_('Description'))
    url_location = models.URLField(_('URL carte lieu'))

    class MetaData:
        list_display = [
            ('name', _(u'Nom')),
        ]
        details_display = list_display + [
            ('description', _(u'Description')),
            ('url_location', _(u'URL carte lieu')),
        ]

        default_sort = "[1, 'asc']"  # name

        filter_fields = ('name', 'description')

        base_title = _(u'Lieux')
        list_title = _(u'Liste des lieux')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-location-arrow'

        menu_id = 'menu-vehicles-location'

        help_list = _(u"""Les lieux de récupération des locations""")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name
