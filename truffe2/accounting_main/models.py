# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.db import models


from accounting_core.utils import AccountingYearLinked, CostCenterLinked
from app.utils import get_current_year, get_current_unit
from generic.models import GenericModel, GenericStateModel, FalseFK, GenericContactableModel, GenericGroupsModel, GenericExternalUnitAllowed, GenericModelWithLines, ModelUsedAsLine, GenericModelWithFiles, GenericTaggableObject
from notifications.utils import notify_people, unotify_people
from rights.utils import UnitExternalEditableModel, UnitEditableModel, AgepolyEditableModel


class _AccountingLine(GenericModel, GenericStateModel, AccountingYearLinked, CostCenterLinked, GenericGroupsModel, GenericContactableModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['TRESORERIE', 'SECRETARIAT']
        world_ro_access = False

    unit = FalseFK('units.models.Unit')
    account = FalseFK('accounting_core.models.Account', verbose_name=_(u'Compte de CG'))
    date = models.DateField()
    tva = models.DecimalField(_('TVA'), max_digits=20, decimal_places=2)
    text = models.CharField(max_length=2048)
    output = models.DecimalField(_(u'Débit'), max_digits=20, decimal_places=2)
    input = models.DecimalField(_(u'Crédit'), max_digits=20, decimal_places=2)
    current_sum = models.DecimalField(_('Situation'), max_digits=20, decimal_places=2)

    class Meta:
        abstract = True

    class MetaEdit:
        pass

    class MetaData:
        list_display = [
            ('date', _(u'Date')),
            ('account', _(u'Compte de CG')),
            ('text', _(u'Text')),
            ('tva', _(u'% TVA')),
            ('get_output_display', _(u'Débit')),
            ('get_input_display', _(u'Crédit')),
            ('get_current_sum_display', _(u'Situation')),
            ('status', _(u'Statut')),
        ]

        forced_widths = {
            '1': '100px',
            '2': '300px',
            '4': '75px',
            '5': '75px',
            '6': '75px',
            '7': '75px',
            '8': '75px',
            '9': '75px',
        }

        default_sort = "[1, 'desc']"  # date
        filter_fields = ('date', 'text', 'tva', 'output', 'input', 'current_sum')

        details_display = list_display

        base_title = _(u'Comptabilité')
        list_title = _(u'Liste des entrées de la comptabilité')
        base_icon = 'fa fa-list-ol'
        elem_icon = 'fa fa-ellipsis-horizontal'

        menu_id = 'menu-compta-compta'
        not_sortable_colums = []
        trans_sort = {'get_output_display': 'output', 'get_input_display': 'input', 'get_current_sum_display': 'current_sum'}
        safe_fields = ['get_output_display', 'get_input_display', 'get_current_sum_display']
        datetime_fields = ['date']

        has_unit = True

        help_list = _(u"""Les lignes de la compta de l'AGEPoly.

Tu peux (et tu dois) valider les lignes ou signaler les erreurs via les boutons corespondants.""")

    class MetaState:

        states = {
            '0_imported': _(u'En attente'),
            '1_valided': _(u'Validé'),
            '2_error': _(u'Erreur'),
        }

        default = '0_imported'

        states_texts = {
            '0_imported': _(u'La ligne viens d\'être importée'),
            '1_valided': _(u'La ligne est validée'),
            '2_error': _(u'La ligne est fausse et nécessaire une correction'),
        }

        states_links = {
            '0_imported': ['1_valided', '2_error'],
            '1_valided': ['2_error'],
            '2_error': ['1_valided'],
        }

        states_colors = {
            '0_imported': 'primary',
            '1_valided': 'success',
            '2_error': 'danger',
        }

        states_icons = {
        }

        list_quick_switch = {
            '0_imported': [('2_error', 'fa fa-warning', _(u'Signaler une erreur')), ('1_valided', 'fa fa-check', _(u'Marquer comme validé')), ],
            '1_valided': [('2_error', 'fa fa-warning', _(u'Signaler une erreur')), ],
            '2_error': [('1_valided', 'fa fa-check', _(u'Marquer comme validé')), ],
        }

        states_default_filter = '0_imported,1_valided,2_error'
        states_default_filter_related = '0_imported,1_valided,2_error'
        status_col_id = 6

    def may_switch_to(self, user, dest_state):

        return super(_AccountingLine, self).rights_can_EDIT(user) and super(_AccountingLine, self).may_switch_to(user, dest_state)

    def can_switch_to(self, user, dest_state):

        if not super(_AccountingLine, self).rights_can_EDIT(user):
            return (False, _('Pas les droits.'))

        return super(_AccountingLine, self).can_switch_to(user, dest_state)

    def rights_can_EDIT(self, user):
        return False  # Never !

    def rights_can_DISPLAY_LOG(self, user):
        """Always display log, even if current state dosen't allow edit"""
        return super(_AccountingLine, self).rights_can_EDIT(user)

    def __unicode__(self):
        return u'{}: {} (-{}/+{})'.format(self.date, self.text, self.output, self.input)

    def get_output_display(self):
        if self.output:
            return '<span class="txt-color-red">{}</span>'.format(self.output)
        else:
            return ''

    def get_input_display(self):
        if self.input:
            return '<span class="txt-color-green">{}</span>'.format(self.input)
        else:
            return ''

    def get_current_sum_display(self):
        if self.current_sum > 0:
            return '<span class="txt-color-green">{}</span>'.format(self.current_sum)
        elif self.current_sum < 0:
            return '<span class="txt-color-red">{}</span>'.format(self.current_sum)
        else:
            return '0.00'
