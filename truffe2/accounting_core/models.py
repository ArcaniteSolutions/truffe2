# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


from generic.models import GenericModel, GenericStateModel
from rights.utils import AgepolyEditableModel
from accounting_core.utils import AccountingYearLinked


class _AccountingYear(GenericModel, GenericStateModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'
        world_ro_access = True

    name = models.CharField(max_length=255, unique=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    class MetaData:
        list_display = [
            ('name', _('Nom de l\'année comptable')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]
        details_display = list_display
        filter_fields = ('name', 'status')

        base_title = _(u'Années Comptables')
        list_title = _(u'Liste des années comptables')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-calendar-o'

        menu_id = 'menu-compta-anneecomptable'

        datetime_fields = ['start_date', 'end_date']

        help_list = _(u"""Les années comptables définissent les périodes d'exercices dans tous les documents comptables.""")

    class MetaState:

        states = {
            '0_preparing': _(u'En préparation'),
            '1_active': _(u'Année active'),
            '2_closing': _(u'En clôture'),
            '3_archived': _(u'Année archivée'),
        }

        default = '0_preparing'

        states_texts = {
            '0_preparing': _(u'L\'année est en cours de création et n\'est pas publique.'),
            '1_active': _(u'L\'année est active.'),
            '2_closing': _(u'L\'année est en train d\'être clôturée.'),
            '3_archived': _(u'L\'année est archivé. Il n\'est plus possible de faire des modifications.'),
        }

        states_links = {
            '0_preparing': ['1_active'],
            '1_active': ['2_closing'],
            '2_closing': ['3_archived'],
            '3_archived': [],
        }

        states_colors = {
            '0_preparing': 'primary',
            '1_active': 'success',
            '2_closing': 'warning',
            '3_archived': 'default',
        }

        states_icons = {
            '0_preparing': '',
            '1_active': '',
            '2_closing': '',
            '3_archived': '',
        }

        list_quick_switch = {
            '0_preparing': [('1_active', 'fa fa-check', _(u'Rendre l\'année active')), ],
            '1_active': [('2_closing', 'fa fa-check', _(u'Passer l\'année en clôture')), ],
            '2_closing': [('3_archived', 'fa fa-check', _(u'Archiver l\'année')), ],
            '3_archived': [],
        }

        states_default_filter = '0_preparing,1_active,2_closing'
        states_default_filter_related = '1_active,2_closing,3_archived'
        status_col_id = 3

    def may_switch_to(self, user, dest_state):

        return self.rights_can('EDIT', user)

    def can_switch_to(self, user, dest_state):

        if self.status == '3_archived' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if int(dest_state[0]) - int(self.status[0]) != 1 and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sauter des étapes ou revenir en arrière.'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

        return super(_AccountingYear, self).can_switch_to(user, dest_state)

    class MetaEdit:
        datetime_fields = ['start_date', 'end_date']

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def rights_can_EDIT(self, user):
        # On ne peut éditer/supprimer que les années en préparation

        if self.status == '0_preparing':
            return super(_AccountingYear, self).rights_can_EDIT(user)

        return False

    @classmethod
    def build_year_menu(cls, mode, user):

        retour = []

        retour += list(cls.objects.filter(status='1_active').order_by('-end_date'))
        retour += list(cls.objects.filter(status='2_closing').order_by('-end_date'))

        # On peut sélectionner les années en préparation que si on est
        # trésorie du comité agepoly ou super_user
        if user.is_superuser or cls().rights_in_root_unit(user, 'TRESORERIE'):
            retour += list(cls.objects.filter(status='0_preparing').order_by('-end_date'))

        # On peut sélectionner les années archivée qu'en list (sauf si on est
        # super_user)
        if mode == 'LIST' or user.is_superuser:
            retour += list(cls.objects.filter(status='3_archived').order_by('-end_date'))

        return retour


class _DummyPony(GenericModel, AccountingYearLinked, AgepolyEditableModel):
    """Ceci est une class de démo pour implémenter AccountingYearLinked avant la finalisation des autres modules comptables

    Il faudra supprimer ce modèle en phase de production
    """

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'
        world_ro_access = True

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    class MetaData:
        list_display = [
            ('name', _('Nom')),
        ]
        details_display = list_display
        filter_fields = ('name')

        base_title = _(u'Poney comptable')
        list_title = _(u'Liste des poneys comptables')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-smile-o'

        menu_id = 'menu-compta-dummypony'

        help_list = _(u"""Class de test pour AccountingYearLinked""")
