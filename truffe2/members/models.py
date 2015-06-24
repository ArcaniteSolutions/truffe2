# -*- coding: utf-8 -*-

from django import forms
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from app.utils import get_current_unit
from generic.models import GenericModel, GenericStateModel, GenericGroupsModel, FalseFK
from rights.utils import UnitEditableModel


class _MemberSet(GenericModel, GenericStateModel, GenericGroupsModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['INFORMATIQUE', 'PRESIDENCE']
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255)
    unit = FalseFK('units.models.Unit', verbose_name=_(u'Unité'))
    generates_accred = models.BooleanField(_(u'Génère des accreds'), default=True)
    generated_accred_type = FalseFK('units.models.Role', blank=True, null=True, verbose_name=_(u'Accréditation générée pour les membres'))
    ldap_visible = models.BooleanField(_(u'Rend les accreds visibles dans l\'annuaire'), default=False)
    handle_fees = models.BooleanField(_(u'Gestion des cotisations'), default=False)

    class MetaData:
        list_display = [
            ('name', _('Nom du groupe de membres')),
            ('generates_accred', _(u'Génère une accréditation')),
            ('ldap_visible', _(u'Visible dans l\'annuaire EPFL')),
            ('handle_fees', _(u'Gestion des cotisations')),
            ('status', _('Statut')),
        ]
        details_display = list_display
        details_display.insert(2, ('generated_accred_type', _(u'Type généré')))
        filter_fields = ('name', 'status')

        base_title = _('Groupes de Membres')
        list_title = _('Liste des groupes de membre')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-male'

        menu_id = 'menu-members-memberset'

        yes_or_no_fields = ['generates_accred', 'ldap_visible', 'handle_fees']

        has_unit = True

        help_list = _(u"""Les groupes de membres représentent l'ensemble des membres des différentes unités de l'AGEPoly.
Par exemple, ils peuvent contenir les membres d'honneurs d'une unité ou les membres qui cotisent.
Les groupes peuvent générer une accréditation EPFL pour leurs membres et gérer les cotisations suivant leur état.""")

    class MetaState:

        states = {
            '0_preparing': _(u'En préparation'),
            '1_active': _(u'Actif'),
            '2_archived': _(u'Archivé'),
        }

        default = '0_preparing'

        states_texts = {
            '0_preparing': _(u'Le groupe de membres est en cours de création et n\'est pas public.'),
            '1_active': _(u'Le groupe de membres est actif.'),
            '2_archived': _(u'Le groupe de membres est archivé.'),
        }

        states_links = {
            '0_preparing': ['1_active'],
            '1_active': ['2_archived'],
            '2_archived': [],
        }

        states_colors = {
            '0_preparing': 'primary',
            '1_active': 'success',
            '2_archived': 'default',
        }

        states_icons = {
            '0_preparing': '',
            '1_active': '',
            '2_archived': '',
        }

        list_quick_switch = {
            '0_preparing': [('1_active', 'fa fa-check', _(u'Rendre le groupe de membres actif')), ],
            '1_active': [('2_archived', 'fa fa-check', _(u'Archiver le groupe de membres')), ],
            '2_archived': [],
        }

        states_default_filter = '0_preparing,1_active'
        states_default_filter_related = '1_active,2_archived'
        status_col_id = 3

    def genericFormExtraClean(self, data, form):
        """Check if accred corresponds to generation constraints & that unique_together is fulfiled"""
        from members.models import MemberSet

        if 'generates_accred' in form.fields:
            if data['generates_accred'] and data['generated_accred_type'] is None:
                raise forms.ValidationError(_(u'Accréditation nécessaire pour l\'attribuer aux membres.'))

            if 'generates_accred' not in data:  # If no accred generation, both other fields are Blank/False
                data['generated_accred_type'] = ''
                if 'ldap_visible' in data:
                    del data['ldap_visible']

        if MemberSet.objects.exclude(pk=self.pk).filter(unit=get_current_unit(form.truffe_request), name=data['name']).count():
            raise forms.ValidationError(_(u'L\'unité possède déjà un groupe avec ce nom.'))  # Potentiellement parmi les supprimées

    def genericFormExtraInit(self, form, *args, **kwargs):
        """Reduce the list of possible accreds to the official ones at EPFL"""
        from units.models import Role

        form.fields['generated_accred_type'].queryset = Role.objects.exclude(id_epfl='')

    def may_switch_to(self, user, dest_state):

        return self.rights_can('EDIT', user)

    def can_switch_to(self, user, dest_state):

        if self.status == '2_archived' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if int(dest_state[0]) - int(self.status[0]) != 1 and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sauter des étapes ou revenir en arrière.'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

        return super(_MemberSet, self).can_switch_to(user, dest_state)

    class Meta:
        abstract = True
        unique_together = ("name", "unit")

    def __unicode__(self):
        return u"{} ({})".format(self.name, self.unit)

    def rights_can_EDIT(self, user):
        # On ne peut pas éditer/supprimer les groupes archivés.

        if self.status == '2_archived':
            return False
        return super(_MemberSet, self).rights_can_EDIT(user)


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    group = models.ForeignKey('MemberSet', verbose_name=_('Groupe de membres'))
    start_date = models.DateTimeField(_('Date d\'ajout au groupe'), auto_now_add=True)
    end_date = models.DateTimeField(_('Date de retrait du groupe'), blank=True, null=True)
    payed_fees = models.BooleanField(_(u'A payé sa cotisation'), default=False)

    def payed_due_fees(self):
        """Return the status of fees if MemberSet handle fees."""
        if self.group.handle_fees:
            return self.payed_fees
        return None
