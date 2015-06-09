from django.db import models
from django.utils.translation import ugettext_lazy as _


from generic.models import GenericModel, GenericStateModel, GenericGroupsModel, FalseFK
from rights.utils import UnitEditableModel


class _MemberSet(GenericModel, GenericStateModel, GenericGroupsModel, UnitEditableModel):
    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['INFORMATIQUE', 'PRESIDENCE']
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255, unique=True)
    generates_accred = models.BooleanField(_(u'Génère des accreds'), default=True)
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
        details_display = list_display
        filter_fields = ('name', 'status')

        base_title = _('Groupes de Membres')
        list_title = _('Liste des groupes de membre')
        base_icon = 'fa fa-users'
        elem_icon = 'fa fa-child'

        menu_id = 'menu-membres-membreset'

        help_list = _(u"""Les groupes de membres représentent l'ensemble des membres des différentes unités de l'AGEPoly.
Par exemple, ils peuvent contenir les membres d'honneurs d'une unité ou les membres qui cotisent.""")

    class MetaState:

        states = {
            '0_preparing': _(u'En préparation'),
            '1_active': _(u'Actif'),
            '2_achived': _(u'Archivé'),
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
        return self.name

    def rights_can_EDIT(self, user):
        # On ne peut pas éditer/supprimer les groupes archivés.

        if self.status == '2_archived':
            return False
        return super(_MemberSet, self).rights_can_EDIT(user)


class _Membership(GenericModel, GenericGroupsModel, UnitEditableModel):
    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['INFORMATIQUE', 'PRESIDENCE']
        world_ro_access = True

    user = FalseFK('users.models.TruffeUser', verbose_name=_('Membre'))
    group = FalseFK('members.models.MemberSet', verbose_name=_('Groupe de membres'))
    adding_date = models.DateTimeField(_('Date d\'ajout au groupe'), auto_now_add=True)
    payed_fees = models.BooleanField(_('A payé sa cotisation'), default=False)


    class MetaData:
        list_display = [
            ('user', _('Membre du groupe')),
            ('generates_accred', _(u'Génère une accréditation EPFL')),
            ('ldap_visible', _(u'Rend l\'accréditation visible dans l\'annuaire EPFL')),
            ('handle_fees', _(u'Gère les cotisations des membres')),
            ('status', _('Statut')),
        ]
        details_display = list_display
        filter_fields = ('user', 'status')

        base_title = _('Gestion des membres')
        list_title = _('Liste des membres du groupe')
        base_icon = 'fa fa-users'
        elem_icon = 'fa fa-child'

        menu_id = 'menu-membres-membreship'

        help_list = _(u"""Les groupes de membres représentent l'ensemble des membres des différentes unités de l'AGEPoly.
Par exemple, ils peuvent contenir les membres d'honneurs d'une unité ou les membres qui cotisent.""")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name
