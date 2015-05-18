# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, GenericStateUnitValidable, FalseFK, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericExternalUnitAllowed, GenericDelayValidable, GenericDelayValidableInfo
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django.core.urlresolvers import reverse


from rights.utils import UnitEditableModel, UnitExternalEditableModel
from generic.templatetags.generic_extras import html_check_and_safe


class _Room(GenericModel, GenericGroupsModel, UnitEditableModel, GenericDelayValidableInfo):

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

        details_display = list_display + [
            ('description', _('Description')),
            ('conditions', _('Conditions')),
            ('conditions_externals', _('Conditions pour les externes')),
            ('max_days', _(u'Nombre maximum de jours de réservation')),
            ('max_days_externals', _(u'Nombre maximum de jours de réservation (externes)')),
            ('minimum_days_before', _(u'Nombre de jours minimum avant réservation')),
            ('minimum_days_before_externals', _(u'Nombre de jours minimum avant réservation (externes)')),
            ('maximum_days_before', _(u'Nombre de jours maximum avant réservation')),
            ('maximum_days_before_externals', _(u'Nombre de jours maximum avant réservation (externes)')),
        ]
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


class _RoomReservation(GenericModel, GenericDelayValidable, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericStateUnitValidable, GenericStateModel, GenericExternalUnitAllowed, UnitExternalEditableModel):

    class MetaRightsUnit(UnitExternalEditableModel.MetaRightsUnit):
        access = 'LOGISTIQUE'
        moderation_access = 'LOGISTIQUE'

    room = FalseFK('logistics.models.Room', verbose_name=_('Salle'))

    title = models.CharField(_('Titre'), max_length=255)

    start_date = models.DateTimeField(_(u'Date de début'))
    end_date = models.DateTimeField(_(u'Date de fin'))

    raison = models.TextField(help_text=_(u'Explique pourquoi tu as besion (manifestation par ex.)'))
    remarks = models.TextField(_('Remarques'), blank=True, null=True)

    class MetaData:

        list_display_base = [
            ('title', _('Titre')),
            ('get_unit_name', _(u'Nom de l\'unité')),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]

        list_display = [list_display_base[0]] + [('room', _(u'Salle')), ] + list_display_base[1:]
        list_display_related = [list_display_base[0]] + [('get_room_link', _(u'Salle')), ] + list_display_base[1:]

        details_display = list_display_base + [('get_room_infos', _('Salle')), ('raison', _('Raison')), ('remarks', _('Remarques')), ('get_conflits', _('Conflits'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _(u'Réservation de salle')
        list_title = _(u'Liste de toutes les réservations de salles')
        list_related_title = _(u'Liste de toutes les réservations des salles de mon unité')
        calendar_title = _(u'Calendrier des réservations de salles')
        calendar_related_title = _(u'Calendrier des réservations des salles de mon unité')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-hospital'

        safe_fields = ['get_unit_name', 'get_room_link']

        menu_id = 'menu-logistics-room-reservation'
        menu_id_related = 'menu-logistics-room-reservation-related'
        menu_id_calendar = 'menu-logistics-room-reservation-calendar'
        menu_id_calendar_related = 'menu-logistics-room-reservation-calendar-related'

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

        trans_sort = {'get_unit_name': 'unit__name', 'get_room_link': 'room__title'}

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

        only_if = {
            'remarks': lambda (obj, user): obj.status == '2_online' and obj.rights_can('VALIDATE', user),
            'room': lambda (obj, user): obj.status == '0_draft',
        }

    class Meta:
        abstract = True

    class MetaState(GenericStateUnitValidable.MetaState):
        unit_field = 'room.unit'
        linked_model = 'logistics.models.Room'

    def __unicode__(self):
        return self.title

    def genericFormExtraClean(self, data, form):
        """Check if select room is available"""

        from django import forms

        if 'room' in form.fields:

            if 'room' not in data or not data['room'].active or data['room'].deleted:
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

    def get_room_link(self):
        return '<a href="%s">%s</a>' % (reverse('logistics.views.room_show', args=(self.room.pk,)), self.room,)


class _Supply(GenericModel, GenericGroupsModel, UnitEditableModel, GenericDelayValidableInfo):

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

        details_display = list_display + [
            ('description', _('Description')),
            ('conditions', _('Conditions')),
            ('conditions_externals', _('Conditions pour les externes')),
            ('max_days', _(u'Nombre maximum de jours de réservation')),
            ('max_days_externals', _(u'Nombre maximum de jours de réservation (externes)')),
            ('minimum_days_before', _(u'Nombre de jours minimum avant réservation')),
            ('minimum_days_before_externals', _(u'Nombre de jours minimum avant réservation (externes)')),
            ('maximum_days_before', _(u'Nombre de jours maximum avant réservation')),
            ('maximum_days_before_externals', _(u'Nombre de jours maximum avant réservation (externes)')),
        ]
        filter_fields = ('title', 'description', 'conditions', 'conditions_externals')

        base_title = _(u'Matériel')
        list_title = _(u'Liste de tout le matériel réservable')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-umbrella'

        menu_id = 'menu-logistics-supply'

        yes_or_no_fields = ['active', 'allow_externals']
        html_fields = ('description', 'conditions', 'conditions_externals')


        has_unit = True

        help_list = _(u"""La liste du matériel réservable, gérés par l'unité en cours.

N'importe quelle unité peut mettre à disposition du matériel et est responsable de la modération des réservations.""")

    class MetaEdit:
        html_fields = ('description', 'conditions', 'conditions_externals')

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _SupplyReservation(GenericModel, GenericDelayValidable, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericStateUnitValidable, GenericStateModel, GenericExternalUnitAllowed, UnitExternalEditableModel):

    class MetaRightsUnit(UnitExternalEditableModel.MetaRightsUnit):
        access = 'LOGISTIQUE'
        moderation_access = 'LOGISTIQUE'

    supply = FalseFK('logistics.models.Supply', verbose_name=_(u'Matériel'))

    title = models.CharField(_('Titre'), max_length=255)

    start_date = models.DateTimeField(_(u'Date de début'))
    end_date = models.DateTimeField(_(u'Date de fin'))

    raison = models.TextField(help_text=_(u'Explique pourquoi tu as besion (manifestation par ex.)'))
    remarks = models.TextField(_('Remarques'), blank=True, null=True)

    class MetaData:

        list_display_base = [
            ('title', _('Titre')),
            ('get_unit_name', _(u'Nom de l\'unité')),
            ('start_date', _('Date debut')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]

        list_display = [list_display_base[0]] + [('supply', _(u'Matériel')), ] + list_display_base[1:]
        list_display_related = [list_display_base[0]] + [('get_supply_link', _(u'Matériel')), ] + list_display_base[1:]

        details_display = list_display_base + [('get_supply_infos', _('Matériel')), ('raison', _('Raison')), ('remarks', _('Remarques')), ('get_conflits', _('Conflits'))]
        filter_fields = ('title', 'start_date', 'end_date', 'status')

        base_title = _(u'Réservation de matériel')
        list_title = _(u'Liste de toutes les réservations de matériel')
        list_related_title = _(u'Liste de toutes les réservations du matériel de mon unité')
        calendar_title = _(u'Calendrier des réservations de matériel')
        calendar_related_title = _(u'Calendrier des réservations du matériel de mon unité')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-umbrella'

        safe_fields = ['get_unit_name', 'get_supply_link']

        menu_id = 'menu-logistics-supply-reservation'
        menu_id_related = 'menu-logistics-supply-reservation-related'
        menu_id_calendar = 'menu-logistics-supply-reservation-calendar'
        menu_id_calendar_related = 'menu-logistics-supply-reservation-calendar-related'

        has_unit = True

        html_fields = ('get_supply_infos', 'get_conflits')
        datetime_fields = ('start_date', 'end_date')

        related_name = _(u'Matériel')

        help_list = _(u"""Les réservation de matériel.

Les réservations sont soumises à modération par l'unité lié au matériel.

Tu peux gérer ici la liste de tes réservation pour l'unité en cours (ou une unité externe).""")

        help_list_related = _(u"""Les réservation du matériel de l'unité.

Les réservations sont soumises à modération par l'unité lié à au matériel.

Tu peux gérer ici la liste de réservation du matériel de l'unité en cours.""")

        trans_sort = {'get_unit_name': 'unit__name', 'get_room_link': 'room__title'}

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

        only_if = {
            'remarks': lambda (obj, user): obj.status == '2_online' and obj.rights_can('VALIDATE', user),
            'supply': lambda (obj, user): obj.status == '0_draft',
        }

    class Meta:
        abstract = True

    class MetaState(GenericStateUnitValidable.MetaState):
        unit_field = 'supply.unit'
        linked_model = 'logistics.models.Supply'

    def __unicode__(self):
        return self.title

    def genericFormExtraClean(self, data, form):
        """Check if select supply is available"""

        from django import forms

        if 'supply' in form.fields:

            if 'supply' not in data or not data['supply'].active or data['supply'].deleted:
                raise forms.ValidationError(_(u'Matériel non disponible'))

            if not self.unit and not data['supply'].allow_externals:
                raise forms.ValidationError(_(u'Matériel non disponible'))

    def get_supply_link(self):
        return '<a href="%s">%s</a>' % (reverse('logistics.views.supply_show', args=(self.supply.pk,)), self.supply,)

    def get_supply_infos(self):
        """Affiche les infos sur le matériel pour une réserversation"""

        tpl = mark_safe('<div style="margin-top: 5px;">%s, %s <span class="label label-info">%s</span></div>' % (escape(self.supply.title), _(u'géré par'), escape(self.supply.unit.name),))

        return tpl

    def get_conflits(self):

        liste = self.supply.supplyreservation_set.exclude(pk=self.pk).filter(status__in=['1_asking', '2_online']).filter(end_date__gt=self.start_date, start_date__lt=self.end_date)

        if not liste:
            return mark_safe('<span class="txt-color-green"><i class="fa fa-check"></i> %s</span>' % (unicode(_('Pas de conflits !')),))
        else:
            retour = '<span class="txt-color-red"><i class="fa fa-warning"></i> %s</span><ul>' % (unicode(_(u'Il y a d\'autres réservations en même temps !')),)

            for elem in liste:
                retour += u'<li><span class="label label-%s"><i class="%s"></i> %s</span> %s pour l\'unité %s  <span data-toggle="tooltip" data-placement="right" title="Du %s au %s"><i class="fa fa-clock-o"></i> </span></li>' % (elem.status_color(), elem.status_icon(), elem.get_status_display(), elem, elem.get_unit_name(), localtime(elem.start_date), localtime(elem.end_date),)

            retour += '</ul>'

            return retour
