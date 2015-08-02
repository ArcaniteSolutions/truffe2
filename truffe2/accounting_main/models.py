# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.forms import CharField, Form, Textarea, BooleanField


import collections
import json

from accounting_core.utils import AccountingYearLinked, CostCenterLinked
from accounting_core.models import AccountingGroupModels
from app.utils import get_current_year, get_current_unit
from generic.models import GenericModel, GenericStateModel, FalseFK, GenericContactableModel, GenericGroupsModel, GenericExternalUnitAllowed, GenericModelWithLines, ModelUsedAsLine, GenericModelWithFiles, GenericTaggableObject
from notifications.utils import notify_people, unotify_people
from rights.utils import UnitExternalEditableModel, UnitEditableModel, AgepolyEditableModel
from users.models import TruffeUser


class _AccountingLine(GenericModel, GenericStateModel, AccountingYearLinked, CostCenterLinked, GenericGroupsModel, AccountingGroupModels, GenericContactableModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['TRESORERIE', 'SECRETARIAT']
        world_ro_access = False

    class MetaRights(UnitEditableModel.MetaRights):
        linked_unit_property = 'costcenter.unit'

    account = FalseFK('accounting_core.models.Account', verbose_name=_(u'Compte de CG'))
    date = models.DateField()
    tva = models.DecimalField(_('TVA'), max_digits=20, decimal_places=2)
    text = models.CharField(max_length=2048)
    output = models.DecimalField(_(u'Débit'), max_digits=20, decimal_places=2)
    input = models.DecimalField(_(u'Crédit'), max_digits=20, decimal_places=2)
    current_sum = models.DecimalField(_('Situation'), max_digits=20, decimal_places=2)
    document_id = models.PositiveIntegerField(_(u'Numéro de pièce comptable'), blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    class MetaEdit:
        pass

    class MetaData:
        list_display = [
            ('date', _(u'Date')),
            ('account', _(u'Compte de CG')),
            ('document_id', _(u'Pièce comptable')),
            ('text', _(u'Texte')),
            ('tva', _(u'% TVA')),
            ('get_output_display', _(u'Débit')),
            ('get_input_display', _(u'Crédit')),
            ('get_current_sum_display', _(u'Situation')),
            ('status', _(u'Statut')),
        ]

        forced_widths = {
            '1': '100px',
            '2': '300px',
            '3': '75px',
            '5': '75px',
            '6': '75px',
            '7': '75px',
            '8': '75px',
            '9': '75px',
            '10': '75px',
        }

        default_sort = "[0, 'desc']"  # order
        filter_fields = ('date', 'text', 'tva', 'output', 'input', 'current_sum')

        details_display = list_display + [
            ('costcenter', _(u'Centre de coûts')),
        ]

        base_title = _(u'Comptabilité')
        list_title = _(u'Liste des entrées de la comptabilité')
        base_icon = 'fa fa-list-ol'
        elem_icon = 'fa fa-ellipsis-horizontal'

        menu_id = 'menu-compta-compta'
        not_sortable_colums = []
        trans_sort = {'get_output_display': 'output', 'get_input_display': 'input', 'get_current_sum_display': 'current_sum', 'pk': 'order'}
        safe_fields = ['get_output_display', 'get_input_display', 'get_current_sum_display']
        datetime_fields = ['date']

        has_unit = True

        extradata = 'cost_center_extradata'

        help_list = _(u"""Les lignes de la compta de l'AGEPoly.

Tu peux (et tu dois) valider les lignes ou signaler les erreurs via les boutons corespondants.""")

        @staticmethod
        def extra_args_for_list(request, current_unit, current_year):
            from accounting_core.models import CostCenter
            return {'costcenters': CostCenter.objects.filter(accounting_year=current_year, deleted=False).filter(Q(unit=current_unit) | (Q(unit__parent_hierarchique=current_unit) & Q(unit__is_commission=False))).order_by('account_number')}

        @staticmethod
        def extra_filter_for_list(request, current_unit, current_year, filtering):
            from accounting_core.models import CostCenter
            try:
                cc = get_object_or_404(CostCenter, pk=request.GET.get('costcenter'))
            except:
                cc = None
            return lambda x: filtering(x).filter(costcenter=cc)

    class MetaState:

        states = {
            '0_imported': _(u'En attente'),
            '1_validated': _(u'Validé'),
            '2_error': _(u'Erreur'),
        }

        default = '0_imported'

        states_texts = {
            '0_imported': _(u'La ligne vient d\'être importée'),
            '1_validated': _(u'La ligne est validée'),
            '2_error': _(u'La ligne est fausse et nécessite une correction'),
        }

        states_links = {
            '0_imported': ['1_validated', '2_error'],
            '1_validated': ['2_error'],
            '2_error': ['1_validated'],
        }

        states_colors = {
            '0_imported': 'primary',
            '1_validated': 'success',
            '2_error': 'danger',
        }

        states_icons = {
        }

        list_quick_switch = {
            '0_imported': [('2_error', 'fa fa-warning', _(u'Signaler une erreur')), ('1_validated', 'fa fa-check', _(u'Marquer comme validé')), ],
            '1_validated': [('2_error', 'fa fa-warning', _(u'Signaler une erreur')), ],
            '2_error': [('1_validated', 'fa fa-check', _(u'Marquer comme validé')), ],
        }

        states_default_filter = '0_imported,1_validated,2_error'
        states_default_filter_related = '0_imported,1_validated,2_error'
        status_col_id = 9

        class FormError(Form):
            error = CharField(label=_('Description de l\'erreur'), help_text=_(u'Une erreur sera crée automatiquement, liée à la ligne. Laisse le champ vide si tu ne veux pas créer une erreur (mais ceci est fortement déconseillé)'), required=False, widget=Textarea)

        class FormValid(Form):
            fix_errors = BooleanField(label=_(u'Résoudre les erreurs liées'), help_text=_(u'Fix automatiquement les erreurs liées à la ligne. Attention, des erreurs peuvent être dissociées !'), required=False, initial=True)

        states_bonus_form = {
            '2_error': FormError,
            ('2_error', '1_validated'): FormValid
        }

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
        if self.output and self.input:
            return u'{}: {} (-{}/+{})'.format(self.date, self.text, self.output, self.input)
        elif self.output:
            return u'{}: {} (-{})'.format(self.date, self.text, self.output)
        else:
            return u'{}: {} (+{})'.format(self.date, self.text, self.input)

    def get_output_display(self):
        if self.output:
            return '<span class="txt-color-red">-{}</span>'.format(self.output)
        else:
            return ''

    def get_input_display(self):
        if self.input:
            return '<span class="txt-color-green">{}</span>'.format(self.input)
        else:
            return ''

    def get_current_sum_display(self):
        if self.current_sum < 0:
            return '<span class="txt-color-green">{}</span>'.format(-self.current_sum)
        elif self.current_sum > 0:
            return '<span class="txt-color-red">-{}</span>'.format(-self.current_sum)
        else:
            return '0.00'

    def switch_status_signal(self, request, old_status, dest_status):

        from accounting_main.models import AccountingError, AccountingErrorLogging

        s = super(_AccountingLine, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

        if dest_status == '2_error':

            if request.POST.get('error'):
                ae = AccountingError(initial_remark=request.POST.get('error'), unit=self.costcenter.unit, linked_line=self, accounting_year=self.accounting_year, costcenter=self.costcenter)
                ae.save()
                AccountingErrorLogging(who=request.user, what='created', object=ae).save()

                notify_people(request, u'AccountingError.{}.created'.format(self.costcenter.unit), 'accounting_error_created', ae, ae.build_group_members_for_compta_everyone_with_messages())

            unotify_people(u'AccountingLine.{}.fixed'.format(self.costcenter.unit), self)
            notify_people(request, u'AccountingLine.{}.error'.format(self.costcenter.unit), 'accounting_line_error', self, self.build_group_members_for_compta_everyone())

        if dest_status == '1_validated':

            if old_status == '2_error':
                unotify_people(u'AccountingLine.{}.error'.format(self.costcenter.unit), self)
                notify_people(request, u'AccountingLine.{}.fixed'.format(self.costcenter.unit), 'accounting_line_fixed', self, self.build_group_members_for_compta_everyone())

            if request.POST.get('fix_errors'):

                for error in self.accountingerror_set.filter(deleted=False).exclude(status='2_fixed'):
                    old_status = error.status
                    error.status = '2_fixed'
                    error.save()

                    AccountingErrorLogging(who=request.user, what='state_changed', object=error, extra_data=json.dumps({'old': unicode(error.MetaState.states.get(old_status)), 'new': unicode(error.MetaState.states.get('2_fixed'))})).save()

                    unotify_people(u'AccountingError.{}.created'.format(self.costcenter.unit), error)
                    notify_people(request, u'AccountingError.{}.fixed'.format(self.costcenter.unit), 'accounting_error_fixed', error, error.build_group_members_for_compta_everyone_with_messages())

    def get_errors(self):
        return self.accountingerror_set.filter(deleted=False).order_by('status')

    def __init__(self, *args, **kwargs):
        super(_AccountingLine, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'IMPORT': _(u'Peut importer la compta'),
        })

    def rights_can_IMPORT(self, user):
        return self.rights_in_root_unit(user, ['TRESORERIE', 'SECRETARIAT'])


class _AccountingError(GenericModel, GenericStateModel, AccountingYearLinked, CostCenterLinked, GenericGroupsModel, AccountingGroupModels, GenericContactableModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['TRESORERIE', 'SECRETARIAT']
        world_ro_access = False

    class MetaRights(UnitEditableModel.MetaRights):
        linked_unit_property = 'costcenter.unit'

    linked_line = FalseFK('accounting_main.models.AccountingLine', verbose_name=_(u'Ligne liée'), blank=True, null=True)
    linked_line_cache = models.CharField(max_length=4096)

    initial_remark = models.TextField(_(u'Remarque initiale'), help_text=_(u'Décrit le problème'))

    class Meta:
        abstract = True

    class MetaEdit:
        pass

    class MetaGroups(AccountingGroupModels.MetaGroups):
        pass

    class MetaData:
        list_display = [
            ('get_line_title', _(u'Erreur')),
            ('costcenter', _(u'Centre de coûts')),
            ('get_linked_line', _(u'Ligne')),
            ('status', _(u'Statut')),
        ]

        default_sort = "[0, 'desc']"  # pk
        filter_fields = ('linked_line__text', 'linked_line_cache')

        details_display = list_display + [
            ('initial_remark', _(u'Remarque initiale')),
        ]

        base_title = _(u'Erreurs')
        list_title = _(u'Liste des erreurs de la comptabilité')
        base_icon = 'fa fa-list-ol'
        elem_icon = 'fa fa-warning'

        menu_id = 'menu-compta-errors'
        not_sortable_colums = ['get_line_title', 'costcenter']
        trans_sort = {'get_linked_line': 'linked_line_cache'}
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

        class FormFixed(Form):
            fix_errors = BooleanField(label=_(u'Mettre la ligne liée comme valide'), help_text=_(u'Met automatiquement la ligne liée comme valide. Attention, la ligne n\'est plus forcément liée !'), required=False, initial=True)

        states_bonus_form = {
            '2_fixed': FormFixed
        }

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
        del form.fields['linked_line_cache']
        del form.fields['linked_line']

    def get_linked_line(self):
        if self.linked_line:
            return self.linked_line.__unicode__()
        elif self.linked_line_cache:
            return u'{} (Cache)'.format(self.linked_line_cache)
        else:
            return _(u'(Aucune ligne liée)')

    def save(self, *args, **kwargs):

        if not self.linked_line_cache and self.linked_line:
            self.linked_line_cache = self.linked_line.__unicode__()

        return super(_AccountingError, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(_AccountingError, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'ADD_COMMENT': _(u'Peut ajouter un commentaire'),
        })

        self.MetaGroups.groups_update({
            'compta_everyone_with_messages': _(u'Toutes les personnes liées via la compta (Admin et secrétaires AGEP, trésorier unité, éditeurs de l\'objet) + les personnes ayant commenté'),
        })

    def get_line_title(self):
        return _(u'Erreur #{} du {} signalée par {}'.format(self.pk, str(self.get_creation_date())[:10], self.get_creator()))

    def get_messages(self):
        return self.accountingerrormessage_set.order_by('when')

    def switch_status_signal(self, request, old_status, dest_status):

        s = super(_AccountingError, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

        if dest_status == '2_fixed':

            if request.POST.get('fix_errors'):

                if self.linked_line and not self.linked_line.deleted and self.linked_line.status == '2_error':

                    from accounting_main.models import AccountingLineLogging

                    old_status = self.linked_line.status
                    self.linked_line.status = '1_validated'
                    self.linked_line.save()

                    AccountingLineLogging(who=request.user, what='state_changed', object=self.linked_line, extra_data=json.dumps({'old': unicode(self.linked_line.MetaState.states.get(old_status)), 'new': unicode(self.linked_line.MetaState.states.get('1_validated'))})).save()

                    unotify_people(u'AccountingLine.{}.error'.format(self.costcenter.unit), self.linked_line)
                    notify_people(request, u'AccountingLine.{}.fixed'.format(self.costcenter.unit), 'accounting_line_fixed', self.linked_line, self.linked_line.build_group_members_for_compta_everyone())

            unotify_people(u'AccountingError.{}.created'.format(self.costcenter.unit), self)
            notify_people(request, u'AccountingError.{}.fixed'.format(self.costcenter.unit), 'accounting_error_fixed', self, self.build_group_members_for_compta_everyone_with_messages())

    def create_signal(self, request):
        notify_people(request, u'AccountingError.{}.created'.format(self.costcenter.unit), 'accounting_error_created', self, self.build_group_members_for_compta_everyone_with_messages())

    def build_group_members_for_compta_everyone_with_messages(self):

        retour = self.build_group_members_for_compta_everyone()

        for message in self.accountingerrormessage_set.all():
            if message.author not in retour:
                retour.append(message.author)

        return retour


class AccountingErrorMessage(models.Model):

    author = models.ForeignKey(TruffeUser)
    when = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    error = models.ForeignKey('AccountingError')


class _Budget(GenericModel, GenericStateModel, AccountingYearLinked, CostCenterLinked, UnitEditableModel, GenericContactableModel, GenericTaggableObject, AccountingGroupModels):
    """Modèle pour les budgets"""

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = ['TRESORERIE', 'SECRETARIAT']
        unit_ro_access = True

    name = models.CharField(_(u'Titre du budget'), max_length=255)
    unit = FalseFK('units.models.Unit')

    class MetaData:
        list_display = [
            ('name', _('Titre')),
            ('costcenter', _(u'Centre de coûts')),
            ('status', _('Statut')),
        ]

        details_display = list_display + [('accounting_year', _(u'Année comptable'))]
        filter_fields = ('name', 'costcenter__name', 'costcenter__account_number')

        default_sort = "[0, 'desc']"  # Creation date (pk) descending

        base_title = _(u'Budgets')
        list_title = _(u'Liste des budgets')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-briefcase'

        has_unit = True

        menu_id = 'menu-compta-budget'

        help_list = _(u"""Les budgets permettent de prévoir les dépenses de l'unité sur l'année.

Il est obligatoire de fournir un budget au plus tard 6 semaines après le début du semestre d'automne à l'AGEPoly.""")

    class Meta:
        abstract = True

    class MetaEdit:
        @staticmethod
        def do_extra_post_actions(obj, post_request):
            """Edit budget lines on edit"""
            from accounting_core.models import Account
            from accounting_main.models import BudgetLine

            map(lambda line: line.delete(), list(obj.budgetline_set.all()))  # Remove all previous lines

            lines = collections.defaultdict(dict)
            for (field, value) in post_request.iteritems():

                if field.startswith('account-'):
                    field_arr = field.split('-')
                    lines[field_arr[2]]['type'] = 1 if field_arr[1] == 'incomes' else -1
                    lines[field_arr[2]]['account_pk'] = value

                if field.startswith('description-'):
                    field_arr = field.split('-')
                    if not lines[field_arr[2]] or 'entries' not in lines[field_arr[2]].keys():
                        lines[field_arr[2]]['entries'] = collections.defaultdict(dict)
                    lines[field_arr[2]]['entries'][field_arr[3]]['description'] = value

                if field.startswith('amount-'):
                    field_arr = field.split('-')
                    if not lines[field_arr[2]] or 'entries' not in lines[field_arr[2]].keys():
                        lines[field_arr[2]]['entries'] = collections.defaultdict(dict)
                    lines[field_arr[2]]['entries'][field_arr[3]]['amount'] = value

            for __, line_object in lines.iteritems():
                account = get_object_or_404(Account, pk=line_object['account_pk'])
                coeff = line_object['type']  # -1 for outcomes, 1 for incomes
                entries = sorted(line_object['entries'].items(), key=lambda (x, y): x)
                for entry in entries:
                    if entry[1]['amount']:
                        amount = coeff * abs(float(entry[1]['amount']))
                        BudgetLine(budget=obj, account=account, description=entry[1]['description'], amount=amount).save()

    class MetaState:
        states = {
            '0_draft': _(u'Brouillon'),
            '0_correct': _(u'A corriger'),
            '1_submited': _(u'Budget soumis'),
            '1_private': _(u'Budget privé'),
            '2_treated': _(u'Budget validé'),
        }

        default = '0_draft'

        states_texts = {
            '0_draft': _(u'Le budget est en cours de création et n\'est pas public.'),
            '0_correct': _(u'Le budget doit être corrigé.'),
            '1_submited': _(u'Le budget a été soumis.'),
            '1_private': _(u'Le budget est terminé et privé.'),
            '2_treated': _(u'Le budget a été validé.'),
        }

        states_links = {
            '0_draft': ['1_submited', '1_private'],
            '0_correct': ['1_submited'],
            '1_submited': ['2_treated', '0_correct'],
            '1_private': [],
            '2_treated': [],
        }

        states_colors = {
            '0_draft': 'primary',
            '0_correct': 'warning',
            '1_submited': 'default',
            '1_private': 'info',
            '2_treated': 'success',
        }

        states_icons = {
            '0_draft': '',
            '0_correct': '',
            '1_submited': '',
            '1_private': '',
            '2_treated': '',
        }

        list_quick_switch = {
            '0_draft': [('1_submited', 'fa fa-check', _(u'Soumettre le budget'))],
            '0_correct': [('1_submited', 'fa fa-check', _(u'Soumettre le budget'))],
            '1_submited': [('2_treated', 'fa fa-check', _(u'Marquer le budget comme validé')), ('0_correct', 'fa fa-exclamation', _(u'Demander des corrections'))],
            '1_private': [('0_draft', 'fa fa-mail-reply', _(u'Remodifier'))],
            '2_treated': [],
        }

        states_default_filter = '0_draft,0_correct'
        status_col_id = 3

    def may_switch_to(self, user, dest_state):
        return super(_Budget, self).rights_can_EDIT(user) and super(_Budget, self).may_switch_to(user, dest_state)

    def can_switch_to(self, user, dest_state):
        if self.status == '2_treated' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état traité'))

        if int(dest_state[0]) - int(self.status[0]) != 1 and not user.is_superuser:
            if not (self.status == '1_submited' and dest_state == '0_correct'):  # Exception faite de la correction
                return (False, _(u'Seul un super utilisateur peut sauter des étapes ou revenir en arrière.'))

        if self.status == '1_submited' and not self.rights_in_root_unit(user, self.MetaRightsUnit.access):
            return (False, _(u'Seul un membre du Comité de Direction peut marquer la demande comme validée ou à corriger.'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

        return super(_Budget, self).can_switch_to(user, dest_state)

    def rights_can_EDIT(self, user):
        if int(self.status[0]) > 0:
            return False

        return super(_Budget, self).rights_can_EDIT(user)

    def rights_can_SHOW(self, user):
        if self.status == '1_private' and not self.rights_in_unit(user, self.unit, access=self.MetaRightsUnit.access, no_parent=True):
            return False

        return super(_Budget, self).rights_can_SHOW(user)

    def __unicode__(self):
        return u"{} ({})".format(self.name, self.costcenter)

    def get_total_incomes(self):
        total = 0.0

        for line in self.budgetline_set.all():
            if line.amount > 0:
                total += float(line.amount)
        return total

    def get_total_outcomes(self):
        total = 0.0

        for line in self.budgetline_set.all():
            if line.amount < 0:
                total += abs(float(line.amount))
        return total

    def get_total(self):
        return sum(map(lambda line: line.amount, list(self.budgetline_set.all())))


class BudgetLine(models.Model):
    budget = models.ForeignKey('Budget', verbose_name=_('Budget'))
    account = models.ForeignKey('accounting_core.Account', verbose_name=_('Compte'))

    amount = models.DecimalField(_('Montant'), max_digits=20, decimal_places=2)
    description = models.CharField(max_length=250)

    def __unicode(self):
        return "{} : {} ({} - {})".format(self.budget, self.amount, self.description, self.account.account_number)
