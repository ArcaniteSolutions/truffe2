# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.shortcuts import get_object_or_404


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

        extradata = 'cost_center_extradata'

        help_list = _(u"""Les lignes de la compta de l'AGEPoly.

Tu peux (et tu dois) valider les lignes ou signaler les erreurs via les boutons corespondants.""")

        @staticmethod
        def extra_args_for_list(request, current_unit, current_year):
            from accounting_core.models import CostCenter
            return {'costcenters': CostCenter.objects.filter(unit=current_unit, accounting_year=current_year, deleted=False).order_by('account_number')}

        @staticmethod
        def extra_filter_for_list(request, current_unit, current_year):
            from accounting_core.models import CostCenter
            cc = get_object_or_404(CostCenter, pk=request.GET.get('costcenter'))
            return lambda x: x.filter(costcenter=cc)

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


class _AccountingError(GenericModel, GenericStateModel, AccountingYearLinked, CostCenterLinked, GenericGroupsModel, GenericContactableModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['TRESORERIE', 'SECRETARIAT']
        world_ro_access = False

    unit = FalseFK('units.models.Unit')

    linked_line = FalseFK('accounting_main.models.AccountingLine', verbose_name=_(u'Ligne liée'), blank=True, null=True)
    linked_line_text = models.CharField(max_length=4096)

    initial_remark = models.TextField(_(u'Remarque initiale'), help_text=_(u'Décrit le problème'))

    class Meta:
        abstract = True

    class MetaEdit:
        pass

    class MetaData:
        list_display = [
            ('get_line_title', _(u'Erreur')),
            ('costcenter', _(u'Centre de coûts')),
            ('get_linked_line', _(u'Ligne')),
            ('status', _(u'Statut')),
        ]

        default_sort = "[0, 'desc']"  # pk
        filter_fields = ('linked_line__text', 'linked_line_text')

        details_display = list_display + [
            ('initial_remark', _(u'Remarque initiale')),
        ]

        base_title = _(u'Erreurs')
        list_title = _(u'Liste des erreurs de la comptabilité')
        base_icon = 'fa fa-list-ol'
        elem_icon = 'fa fa-warning'

        menu_id = 'menu-compta-errors'
        not_sortable_colums = ['get_line_title', 'costcenter']
        trans_sort = {'get_linked_line': 'linked_line_text'}
        safe_fields = []

        has_unit = True

        help_list = _(u"""Les erreurs signalées dans la compta de l'AGEPoly.""")

    class MetaState:

        states = {
            '0_drafting': _(u'Établisement du problème'),
            '1_fixing': _(u'En attente de correction'),
            '2_fixed': _(u'Correction effectuée'),
        }

        default = '0_drafting'

        states_texts = {
            '0_drafting': _(u'L\'erreur à été signalée, les détails sont en cours d\'élaboration.'),
            '1_fixing': _(u'L\'erreur à été déterminée et une correction est en attente.'),
            '2_fixed': _(u'L\'erreur à été corrigée.'),
        }

        states_links = {
            '0_drafting': ['1_fixing', '2_fixed'],
            '1_fixing': ['0_drafting', '2_fixed'],
            '2_fixed': ['1_fixing'],
        }

        states_colors = {
            '0_drafting': 'warning',
            '1_fixing': 'danger',
            '2_fixed': 'success',
        }

        states_icons = {
        }

        list_quick_switch = {
            '0_drafting': [('1_fixing', 'fa fa-warning', _(u'Marquer comme \'En attente de correction\'')), ('2_fixed', 'fa fa-check', _(u'Marquer comme corrigé')), ],
            '1_fixing': [('2_fixed', 'fa fa-check', _(u'Marquer comme corrigé')), ],
            '2_fixed': [('1_fixing', 'fa fa-warning', _(u'Marquer comme \'En attente de correction\'')), ],
        }

        states_default_filter = '0_drafting,1_fixing'
        status_col_id = 4

    def may_switch_to(self, user, dest_state):

        return super(_AccountingError, self).rights_can_EDIT(user) and super(_AccountingError, self).may_switch_to(user, dest_state)

    def can_switch_to(self, user, dest_state):

        if not super(_AccountingError, self).rights_can_EDIT(user):
            return (False, _('Pas les droits.'))

        return super(_AccountingError, self).can_switch_to(user, dest_state)

    def rights_can_EDIT(self, user):
        if self.status == '2_fixed':
            return False  # Never !

        return super(_AccountingError, self).rights_can_EDIT(user)

    def rights_can_ADD_COMMENT(self, user):
        return super(_AccountingError, self).rights_can_EDIT(user)

    def rights_can_DISPLAY_LOG(self, user):
        """Always display log, even if current state dosen't allow edit"""
        return super(_AccountingError, self).rights_can_EDIT(user)

    def __unicode__(self):
        return u'Erreur: {}'.format(self.get_linked_line())

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        del form.fields['linked_line_text']
        del form.fields['linked_line']

    def get_linked_line(self):
        if self.linked_line:
            return self.linked_line.__unicode__()
        else:
            return self.linked_line_text or _(u'(Aucune ligne liée)')

    def save(self, *args, **kwargs):

        if not self.linked_line_text and self.linked_line:
            self.linked_line_text = self.linked_line.__unicode__()

        return super(_AccountingError, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(_AccountingError, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'ADD_COMMENT': _(u'Peut ajouter un commentaire'),
        })

    def get_line_title(self):
        return _(u'Erreur #{} du {} signalée par {}'.format(self.pk, str(self.get_creation_date())[:10], self.get_creator()))
