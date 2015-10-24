# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.shortcuts import get_object_or_404


from generic.models import GenericModel, GenericStateModel, FalseFK, GenericGroupsModel, GenericStateRootValidable, GenericGroupsModerableModel, GenericContactableModel, SearchableModel
from rights.utils import AgepolyEditableModel, UnitEditableModel
from users.models import TruffeUser


class _Provider(GenericModel, AgepolyEditableModel, SearchableModel):

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

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u'mobility véhicule'

        fields = [
            'name',
            'description',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def get_types(self):
        return self.vehicletype_set.filter(deleted=False).order_by('name')

    def get_cards(self):
        return self.card_set.filter(deleted=False).order_by('name')


class _VehicleType(GenericModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = True

    provider = FalseFK('vehicles.models.Provider', verbose_name=_('Fournisseur'))
    name = models.CharField(_('Nom'), max_length=255)
    description = models.TextField(_('Description'))

    class MetaData:
        list_display = [
            ('name', _(u'Nom')),
            ('provider', _(u'Fournisseur')),
        ]
        details_display = list_display + [
            ('description', _(u'Description')),
        ]

        default_sort = "[1, 'asc']"  # name

        filter_fields = ('name', 'description', 'provider__name')

        base_title = _(u'Types de véhicule')
        list_title = _(u'Liste des types de véhicules')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-truck'

        menu_id = 'menu-vehicles-type'

        help_list = _(u"""Les différents types de véhicules, par fournisseur""")

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u'mobility véhicule'

        fields = [
            'name',
            'description',
            'provider',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class _Card(GenericModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = False

    provider = FalseFK('vehicles.models.Provider', verbose_name=_('Fournisseur'))
    name = models.CharField(_('Nom'), max_length=255)
    number = models.CharField(_(u'Numéro'), max_length=255)
    description = models.TextField(_('Description'))
    exclusif = models.BooleanField(_('Usage exclusif'), default=True, help_text=_(u'Ne peut pas être utilisé plusieurs fois en même temps ?'))

    class MetaData:
        list_display = [
            ('name', _(u'Nom')),
            ('provider', _(u'Fournisseur')),
            ('number', _(u'Numéro')),
        ]
        details_display = list_display + [
            ('description', _(u'Description')),
            ('exclusif', _(u'Usage exclusif'))
        ]

        default_sort = "[1, 'asc']"  # name

        yes_or_no_fields = ['exclusif']
        filter_fields = ('name', 'number', 'description', 'provider__name')

        base_title = _(u'Cartes')
        list_title = _(u'Liste des cartes')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-credit-card'

        menu_id = 'menu-vehicles-cards'

        help_list = _(u"""Les différentes cartes utilisées pour les réservations""")

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u'mobility véhicule'

        fields = [
            'name',
            'description',
            'provider',
            'number',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'{} ({})'.format(self.name, self.number)


class _Location(GenericModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['LOGISTIQUE', 'SECRETARIAT']
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255)
    description = models.TextField(_('Description'))
    url_location = models.URLField(_('URL carte lieu'), blank=True, null=True)

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

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u'mobility véhicule'

        fields = [
            'name',
            'description',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class _Booking(GenericModel, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericStateRootValidable, GenericStateModel, UnitEditableModel, SearchableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'LOGISTIQUE'
        moderation_access = 'SECRETARIAT'

    unit = FalseFK('units.models.Unit')

    title = models.CharField(_(u'Titre'), max_length=255)
    responsible = models.ForeignKey(TruffeUser, verbose_name=_(u'Responsable'))
    reason = models.TextField(_(u'Motif'))
    remark = models.TextField(_(u'Remarques'), blank=True, null=True)
    remark_agepoly = models.TextField(_(u'Remarques AGEPoly'), blank=True, null=True)

    provider = FalseFK('vehicles.models.Provider', verbose_name=_(u'Fournisseur'))
    vehicletype = FalseFK('vehicles.models.VehicleType', verbose_name=_(u'Type de véhicule'))
    card = FalseFK('vehicles.models.Card', verbose_name=_(u'Carte'), blank=True, null=True)
    location = FalseFK('vehicles.models.Location', verbose_name=_(u'Lieu'), blank=True, null=True)

    start_date = models.DateTimeField(_(u'Début de la réservation'))
    end_date = models.DateTimeField(_(u'Fin de la résrvation'))

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('provider', _('Fournisseur')),
            ('vehicletype', _(u'Type de véhicule')),
            ('status', _('Statut')),
        ]
        details_display = list_display + [
            ('responsible', _('Responsable')),
            ('reason', _('Motif')),
            ('remark', _('Remarques')),
            ('remark_agepoly', _('Remarques AGEPoly')),
            ('card', _('Carte')),
            ('get_location', _('Lieu')),
        ]

        filter_fields = ('title', 'status')

        base_title = _(u'Réservations de véhicule')
        list_title = _(u'Liste de toutes les réservations de véhicules')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-ambulance'

        default_sort = "[3, 'desc']"  # end_date

        menu_id = 'menu-vehicles-booking'
        menu_id_calendar = 'menu-vehicles-booking-calendar'
        menu_id_calendar_related = 'menu-vehicles-booking-calendar-related'

        datetime_fields = ['start_date', 'end_date']
        safe_fields = ['get_location']

        has_unit = True

        help_list = _(u"""Les réservations de véhicules te permettent de demander la location d'un véhicule pour ton unité.

Ils sont soumis à validation par le secrétariat de l'AGEPoly. Il faut toujours faire les réservations le plus tôt possible !""")

        help_list_related = _(u"""La liste de toutes les réservations de véhicules.""")

        @staticmethod
        def extra_args_for_edit(request, current_unit, current_year):
            from vehicles.models import Provider
            return {'providers': Provider.objects.filter(deleted=False).order_by('name')}

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u'mobility véhicule réservation'

        fields = [
            'title',
            'card',
            'provider',
            'location',
            'vehicletype',
            'responsible',
            'remark',
            'reason',
            'remark_agepoly',
        ]

    class MetaState(GenericStateRootValidable.MetaState):

        states_texts = {
            '0_draft': _(u'La réservation est en cours de création et n\'est pas publique.'),
            '1_asking': _(u'La réservation est en cours de modération. Elle n\'est pas éditable. Sélectionner ce statut pour demander une modération !'),
            '2_online': _(u'La résevation est validée. Elle n\'est pas éditable.'),
            '3_archive': _(u'La réservation est archivée. Elle n\'est plus modifiable.'),
            '4_deny': _(u'La modération a été refusée. Le véhicule n\'était probablement pas disponible.'),
        }

        def build_form_validation(request, obj):
            from vehicles.models import Location

            class FormValidation(forms.Form):
                remark_agepoly = forms.CharField(label=_('Remarque'), widget=forms.Textarea, required=False)
                card = forms.ModelChoiceField(label=_(u'Carte'), queryset=obj.provider.get_cards(), required=False)
                location = forms.ModelChoiceField(label=_(u'Lieu'), queryset=Location.objects.filter(deleted=False).order_by('name'), required=False)

            return FormValidation

        states_bonus_form = {
            '2_online': build_form_validation
        }

    def switch_status_signal(self, request, old_status, dest_status):

        from vehicles.models import Location, Card

        if dest_status == '2_online':

            if request.POST.get('remark_agepoly'):
                if self.remark_agepoly:
                    self.remark_agepoly += '\n' + request.POST.get('remark_agepoly')
                else:
                    self.remark_agepoly = request.POST.get('remark_agepoly')
                self.save()

            if request.POST.get('card'):
                self.card = get_object_or_404(Card, pk=request.POST.get('card'), provider=self.provider, deleted=False)
                self.save()

            if request.POST.get('location'):
                self.location = get_object_or_404(Location, pk=request.POST.get('location'), deleted=False)
                self.save()

        s = super(_Booking, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def get_location(self):
        if self.location:
            if self.location.url_location:
                return u'<a href="{}">{}</a>'.format(self.location.url_location, self.location)
            else:
                return self.location.__unicode__()
        else:
            return ''

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        """Remove fields that should be edited by SECRETARIAT CDD only."""

        if not self.rights_in_root_unit(current_user, 'SECRETARIAT'):
            del form.fields['card']
            del form.fields['location']
            del form.fields['remark_agepoly']

        unit_users_pk = map(lambda user: user.pk, self.unit.users_with_access())
        form.fields['responsible'].queryset = TruffeUser.objects.filter(pk__in=unit_users_pk).order_by('first_name', 'last_name')

    def genericFormExtraClean(self, data, form):

        if 'provider' in data:
            if 'card' in data and data['card']:
                if data['card'].provider != data['provider']:
                    raise forms.ValidationError(_(u'La carte n\'est pas lié au fournisseur sélectionné'))
            if 'vehiculetype' in data and data['vehiculetype']:
                if data['vehiculetype'].provider != data['provider']:
                    raise forms.ValidationError(_(u'Le type de véhicule n\'est pas lié au fournisseur sélectionné'))

    def conflicting_reservation(self):
        return self.__class__.objects.exclude(pk=self.pk, deleted=True).filter(status__in=['2_online'], end_date__gt=self.start_date, start_date__lt=self.end_date)
