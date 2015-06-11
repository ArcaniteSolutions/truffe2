# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


from generic.models import GenericModel, GenericStateModel, GenericGroupsModel, FalseFK
from rights.utils import UnitEditableModel


class _MemberSet(GenericModel, GenericStateModel, GenericGroupsModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['INFORMATIQUE', 'PRESIDENCE']
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255, unique=True)
    unit = FalseFK('units.models.Unit', verbose_name=_(u'Unité'))
    generates_accred = models.BooleanField(_(u'Génère des accreds'), default=True)
    generated_accred_type = FalseFK('units.models.Role', blank=True, null=True, verbose_name=_(u'Accréditation générée pour les membres'))
    ldap_visible = models.BooleanField(_(u'Rend les accreds visibles dans l\'annuaire'), default=False)
    handle_fees = models.BooleanField(_(u'Gère les cotisations'), default=False)

    class MetaData:
        list_display = [
            ('name', _('Nom du groupe de membres')),
            ('generates_accred', _(u'Génère une accréditation EPFL')),
            ('ldap_visible', _(u'Rend l\'accréditation visible dans l\'annuaire EPFL')),
            ('handle_fees', _(u'Gère les cotisations des membres')),
            ('status', _('Statut')),
        ]
        details_display = list_display + [('generated_accred_type', _(u'Accréditation générée pour les membres'))]
        filter_fields = ('name', 'status')

        base_title = _('Groupes de Membres')
        list_title = _('Liste des groupes de membre')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-male'

        menu_id = 'menu-members-memberset'

        yes_or_no_fields = ['generates_accred', 'ldap_visible', 'handle_fees']

        has_unit = True

        help_list = _(u"""Les groupes de membres représentent l'ensemble des membres des différentes unités de l'AGEPoly.
Par exemple, ils peuvent contenir les membres d'honneurs d'une unité ou les membres qui cotisent.""")

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

    def __unicode__(self):
        return "{} ({})".format(self.name, self.unit)

    def rights_can_EDIT(self, user):
        # On ne peut pas éditer/supprimer les groupes archivés.

        if self.status == '2_archived':
            return False
        return super(_MemberSet, self).rights_can_EDIT(user)


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    group = models.ForeignKey('MemberSet', verbose_name=_('Groupe de membres'))
    adding_date = models.DateTimeField(_('Date d\'ajout au groupe'), auto_now_add=True)
    payed_fees = models.BooleanField(_(u'A payé sa cotisation'), default=False)

    def payed_due_fees(self):
        """Return the status of fees if MemberSet handle fees."""
        if self.group.handle_fees:
            return self.payed_fees
        return None
