# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, GenericStateUnitValidable, FalseFK, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericExternalUnitAllowed
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


from rights.utils import UnitEditableModel


class _Room(GenericModel, GenericGroupsModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'LOGISTIQUE'

    title = models.CharField(max_length=255)
    description = models.TextField()
    unit = FalseFK('units.models.Unit')

    active = models.BooleanField(_('Actif'), help_text=_(u'Pour désactiver temporairement la posibilité de réserver'), default=True)

    conditions = models.TextField(_(u'Conditions de réservation'), help_text=_(u'Si tu veux préciser des informations sur la réservation de la salle'), blank=True)

    allow_externals = models.BooleanField(_(u'Autoriser les externes'), help_text=_(u'Permet aux externes (pas dans l\'AGEPoly) de réserver la salle'), default=False)
    conditions_externals = models.TextField(_(u'Conditions de réservation pour les externes'), help_text=_(u'Si tu veux préciser des informations sur la réservation de la salle pour les externes. Remplace le champ \'Conditions\' pour les externe si remplis.'), blank=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('active', _('Actif')),
            ('allow_externals', _('Autoriser les externes')),
        ]

        details_display = list_display + [('description', _('Description')), ('conditions', _('Conditions')), ('conditions_externals', _('Conditions pour les externes'))]
        filter_fields = ('title', 'description', 'conditions', 'conditions_externals')

        base_title = _('Salle')
        list_title = _(u'Liste de toutes les salles réservables')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-hospital'

        menu_id = 'menu-logistics-room'

        yes_or_no_fields = ['active', 'allow_externals']
        html_fields = ('description', 'conditions', 'conditions_externals')

        has_unit = True

        help_list = _(u"""Les salles sont la liste des salles réservables, gérés par l'unité en cours.

N'importe quelle unité peut mettre à disposition des salles et est responsable de la modération des réservations.""")

    class MetaEdit:
        html_fields = ('description', 'conditions', 'conditions_externals')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _RoomReservation(GenericModel, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericStateUnitValidable, GenericStateModel, GenericExternalUnitAllowed, UnitEditableModel):

    room = FalseFK('logistics.models.Room')

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    title = models.CharField(max_length=255)
    raison = models.TextField()
    remarks = models.TextField()

    generic_state_unit_field = 'room.unit'

    class MetaData:

        list_display = [
            ('title', _('Titre')),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('status', _('Status')),
        ]

        details_display = list_display + [('room', _('Room')), ('raison', _('Raison')), ('remarks', _('Remarques'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _('Réservation de salle')
        list_title = _(u'Liste de toutes les réservation de salles')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-hospital'

        menu_id = 'menu-logistics-room-reservation'

        has_unit = True

        help_list = _(u"""Les réservation de salles.

Les réservations sont soumises à modération par l'unité lié à la salle.

Tu peux gérer ici la liste de tes réservation pour l'unité en cours (ou une unité externe) et modérer les réservation des autres unités te concernant.""")

    class MetaEdit:
        date_time_fields = ('start_date', 'end_date')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title
