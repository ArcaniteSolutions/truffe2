# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, GenericStateUnitValidable, FalseFK, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericExternalUnitAllowed
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime


from rights.utils import UnitEditableModel, UnitExternalEditableModel
from generic.templatetags.generic_extras import html_check_and_safe


class _Room(GenericModel, GenericGroupsModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'LOGISTIQUE'

    title = models.CharField(_('Titre'), max_length=255)
    description = models.TextField()
    unit = FalseFK('units.models.Unit')

    active = models.BooleanField(_('Actif'), help_text=_(u'Pour désactiver temporairement la posibilité de réserver'), default=True)

    conditions = models.TextField(_(u'Conditions de réservation'), help_text=_(u'Si tu veux préciser les conditions de réservations pour la salle. Tu peux par exemple mettre un lien vers un contrat.'), blank=True)

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


class _RoomReservation(GenericModel, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericStateUnitValidable, GenericStateModel, GenericExternalUnitAllowed, UnitExternalEditableModel):

    class MetaRightsUnit(UnitExternalEditableModel.MetaRightsUnit):
        access = 'LOGISTIQUE'
        moderation_access = 'LOGISTIQUE'

    room = FalseFK('logistics.models.Room', verbose_name=_('Salle'))

    title = models.CharField(_('Titre'), max_length=255)

    start_date = models.DateTimeField(_(u'Date de début'))
    end_date = models.DateTimeField(_(u'Date de fin'))

    raison = models.TextField(help_text=_(u'Explique pourquoi tu as besion (manifestation par ex.)'))
    remarks = models.TextField(_('Remarques'), blank=True, null=True)

    generic_state_unit_field = 'room.unit'

    def generic_set_dummy_unit(self, unit):
        from logistics.models import Room
        r = Room(unit=unit)
        self.room = r

    @staticmethod
    def get_linked_object_class():
        from logistics.models import Room
        return Room

    def get_linked_object(self):
        return self.room

    class MetaData:

        list_display = [
            ('title', _('Titre')),
            ('get_unit_name', 'Non de l\'unité'),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('status', _('Status')),
        ]

        details_display = list_display + [('get_room_infos', _('Salle')), ('raison', _('Raison')), ('remarks', _('Remarques')), ('get_conflits', _('Conflits'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _(u'Réservation de salle')
        list_title = _(u'Liste de toutes les réservations de salles')
        list_related_title = _(u'Liste de toutes les réservations des salles de mon unité')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-hospital'

        safe_fields = ['get_unit_name']

        menu_id = 'menu-logistics-room-reservation'
        menu_id_related = 'menu-logistics-room-reservation-related'

        has_unit = True

        html_fields = ('get_room_infos', 'get_conflits')
        datetime_fields = ('start_date', 'end_date')

        related_name = _('Salle')

        help_list = _(u"""Les réservation de salles.

Les réservations sont soumises à modération par l'unité lié à la salle.

Tu peux gérer ici la liste de tes réservation pour l'unité en cours (ou une unité externe).""")

        help_list_related = _(u"""Les réservation des salles de l'unité.

Les réservations sont soumises à modération par l'unité lié à la salle.

Tu peux gérer ici la liste de réservation des salles de l'unité en cours.""")

    class MetaEdit:
        date_time_fields = ('start_date', 'end_date')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def genericFormExtraClean(self, data):
        """Check if select room is available"""

        from django import forms

        if 'room' not in data or not data['room'].active:
            raise forms.ValidationError(_('Salle non disponible'))

        if not self.unit and not data['room'].allow_externals:
            raise forms.ValidationError(_('Salle non disponible'))

    def get_room_infos(self):
        """Affiche les infos sur la salle pour une réserversation"""

        tpl = mark_safe('<div style="margin-top: 5px;">%s, %s <span class="label label-info">%s</span></div>' % (escape(self.room.title), _(u'gérée par'), escape(self.room.unit.name),))

        return tpl

    def get_conflits(self):

        liste = self.room.roomreservation_set.exclude(pk=self.pk).filter(status__in=['1_asking', '2_online']).filter(end_date__gt=self.start_date, start_date__lt=self.end_date)

        if not liste:
            return mark_safe('<span class="txt-color-green"><i class="fa fa-check"></i> %s</span>' % (unicode(_('Pas de conflits !')),))
        else:
            retour = '<span class="txt-color-red"><i class="fa fa-warning"></i> %s</span><ul>' % (unicode(_(u'Il y a d\'autres réservations en même temps !')),)

            for elem in liste:
                retour += u'<li><span class="label label-%s"><i class="%s"></i> %s</span> %s pour l\'unité %s  <span data-toggle="tooltip" data-placement="right" title="Du %s au %s"><i class="fa fa-clock-o"></i> </span></li>' % (elem.status_color(), elem.status_icon(), elem.get_status_display(), elem, elem.get_unit_name(), localtime(elem.start_date), localtime(elem.end_date),)

            retour += '</ul>'

            return retour
