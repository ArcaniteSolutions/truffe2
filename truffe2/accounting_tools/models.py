# -*- coding: utf-8 -*-

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _

from accounting_core.utils import AccountingYearLinked, CostCenterLinked
from app.utils import get_current_year, get_current_unit
from generic.models import GenericModel, GenericStateModel, FalseFK, GenericContactableModel, GenericGroupsModel, GenericExternalUnitAllowed, GenericModelWithLines, ModelUsedAsLine, GenericModelWithFiles, GenericTaggableObject
from notifications.utils import notify_people, unotify_people
from rights.utils import UnitExternalEditableModel, UnitEditableModel, AgepolyEditableModel


class _Subvention(GenericModel, GenericModelWithFiles, GenericModelWithLines, AccountingYearLinked, GenericStateModel, GenericGroupsModel, UnitExternalEditableModel, GenericExternalUnitAllowed, GenericContactableModel):

    SUBVENTION_TYPE = (
        ('subvention', _(u'Subvention')),
        ('sponsorship', _(u'Sponsoring')),
    )

    class MetaRightsUnit(UnitExternalEditableModel.MetaRightsUnit):
        access = 'TRESORERIE'
        world_ro_access = False

    name = models.CharField(_(u'Nom du projet'), max_length=255)
    amount_asked = models.SmallIntegerField(_(u'Montant demandé'))
    amount_given = models.SmallIntegerField(_(u'Montant attribué'), blank=True, null=True)
    mobility_asked = models.SmallIntegerField(_(u'Montant mobilité demandé'), blank=True, null=True)
    mobility_given = models.SmallIntegerField(_(u'Montant mobilité attribué'), blank=True, null=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    comment_root = models.TextField(_('Commentaire AGEPoly'), blank=True, null=True)
    kind = models.CharField(_(u'Type de soutien'), max_length=15, choices=SUBVENTION_TYPE, blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = (("unit", "unit_blank_name", "accounting_year"),)

    class MetaEdit:
        files_title = _(u'Fichiers')
        files_help = _(u'Envoie les fichiers nécessaires pour ta demande de subvention.')

    class MetaData:
        list_display = [
            ('name', _(u'Projet')),
            ('get_unit_name', _(u'Association / Commission')),
            ('amount_asked', _(u'Montant demandé')),
            ('mobility_asked', _(u'Montant mobilité demandé')),
        ]

        default_sort = "[2, 'asc']"  # unit
        filter_fields = ('name', 'kind', 'unit')

        details_display = list_display + [('description', _(u'Description')), ('accounting_year', _(u'Année comptable'))]
        extra_right_display = {'comment_root': lambda (obj, user): obj.rights_can('LIST', user)}

        files_title = _(u'Fichiers')
        base_title = _(u'Subvention')
        list_title = _(u'Liste des demandes de subvention')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-gift'

        menu_id = 'menu-compta-subventions'
        not_sortable_colums = ['get_unit_name']
        safe_fields = ['get_unit_name']

        has_unit = True

        help_list = _(u"""Les demandes de subvention peuvent être faites par toutes les commissions ou association auprès de l'AGEPoly.""")

    class MetaAccounting:
        copiable = False

    class MetaLines:
        lines_objects = [
            {
                'title': _(u'Evènements'),
                'class': 'accounting_tools.models.SubventionLine',
                'form': 'accounting_tools.forms.SubventionLineForm',
                'related_name': 'events',
                'field': 'subvention',
                'sortable': True,
                'date_fields': ['start_date', 'end_date'],
                'show_list': [
                    ('name', _(u'Titre')),
                    ('start_date', _(u'Du')),
                    ('end_date', _(u'Au')),
                    ('place', _(u'Lieu')),
                    ('nb_spec', _(u'Nb personnes attendues')),
                ]
            },
        ]

    class MetaState:

        states = {
            '0_draft': _(u'Brouillon'),
            '0_correct': _(u'A corriger'),
            '1_submited': _(u'Demande soumise'),
            '2_treated': _(u'Demande traitée'),
        }

        default = '0_draft'

        states_texts = {
            '0_draft': _(u'La demande est en cours de création et n\'est pas publique.'),
            '1_submited': _(u'La demande a été soumise.'),
            '0_correct': _(u'La demande doit être corrigée.'),
            '2_treated': _(u'La demande a été traitée.'),
        }

        states_links = {
            '0_draft': ['1_submited'],
            '0_correct': ['1_submited'],
            '1_submited': ['2_treated', '0_correct'],
            '2_treated': [],
        }

        states_colors = {
            '0_draft': 'primary',
            '1_submited': 'default',
            '0_correct': 'warning',
            '2_treated': 'success',
        }

        states_icons = {
            '0_draft': '',
            '1_submited': '',
            '0_correct': '',
            '2_treated': '',
        }

        list_quick_switch = {
            '0_draft': [('1_submited', 'fa fa-check', _(u'Soumettre la demande'))],
            '0_correct': [('1_submited', 'fa fa-check', _(u'Soumettre la demande'))],
            '1_submited': [('2_treated', 'fa fa-check', _(u'Marquer la demande comme traitée')), ('0_correct', 'fa fa-exclamation', _(u'Demander des corrections'))],
            '2_treated': [],
        }

        states_default_filter = '0_draft,0_correct'
        status_col_id = 3

    def __init__(self, *args, **kwargs):
        super(_Subvention, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'EXPORT': _(u'Peut exporter les éléments'),
        })

    def may_switch_to(self, user, dest_state):

        return self.rights_can('EDIT', user)

    def can_switch_to(self, user, dest_state):

        if self.status == '2_treated' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état traité'))

        if int(dest_state[0]) - int(self.status[0]) != 1 and not user.is_superuser:
            if not (self.status == '1_submited' and dest_state == '0_correct'):  # Exception faite de la correction
                return (False, _(u'Seul un super utilisateur peut sauter des étapes ou revenir en arrière.'))

        if self.status == '1_submited' and not self.rights_in_root_unit(user, self.MetaRightsUnit.access):
            return (False, _(u'Seul un membre du Comité de Direction peut marquer la demande comme traitée ou à corriger.'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

        return super(_Subvention, self).can_switch_to(user, dest_state)

    def __unicode__(self):
        return u"{} {}".format(self.unit, self.accounting_year)

    def genericFormExtraClean(self, data, form):
        """Check that unique_together is fulfiled"""
        from accounting_tools.models import Subvention

        if Subvention.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), unit=get_current_unit(form.truffe_request), unit_blank_name=data['unit_blank_name']).count():
            raise forms.ValidationError(_(u'Une demande de subvention pour cette unité existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        """Remove fields that should be edited by CDD only."""

        if not self.rights_in_root_unit(current_user, self.MetaRightsUnit.access):
            for key in ['amount_given', 'mobility_given', 'comment_root']:
                del form.fields[key]
            form.fields['kind'].widget = forms.HiddenInput()

    def rights_can_EXPORT(self, user):
        return self.rights_in_root_unit(user)

    def get_real_unit_name(self):
        return self.unit_blank_name or self.unit.name

    def total_people(self):
        """Return the total number of expected people among all events"""
        total = 0
        for line in self.events.all():
            total += line.nb_spec
        return total


class SubventionLine(ModelUsedAsLine):
    name = models.CharField(_(u'Nom de l\'évènement'), max_length=255)
    start_date = models.DateField(_(u'Début de l\'évènement'))
    end_date = models.DateField(_(u'Fin de l\'évènement'))
    place = models.CharField(_(u'Lieu de l\'évènement'), max_length=100)
    nb_spec = models.SmallIntegerField(_(u'Nombre de personnes attendues'))

    subvention = models.ForeignKey('Subvention', related_name="events", verbose_name=_(u'Subvention/sponsoring'))

    def __unicode__(self):
        return u"{}:{}".format(self.subvention.name, self.name)


class _Invoice(GenericModel, GenericTaggableObject, CostCenterLinked, GenericModelWithLines, AccountingYearLinked, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'TRESORERIE'

    title = models.CharField(max_length=255)
    unit = FalseFK('units.models.Unit')

    # TODO: Statut (Draft, Sent, TramisMarianne, Reçu), champs pdf

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('costcenter', _(u'Centre de cout')),
        ]
        details_display = list_display
        filter_fields = ('title', )

        base_title = _(u'Facture')
        list_title = _(u'Liste de toutes les factures')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-pencil-square-o'

        default_sort = "[1, 'asc']"  # title

        menu_id = 'menu-compta-invoice'

        has_unit = True

        help_list = _(u"""Factures.""")

    class MetaEdit:
        pass

    class MetaLines:
        lines_objects = [
            {
                'title': _(u'Lignes'),
                'class': 'accounting_tools.models.InvoiceLine',
                'form': 'accounting_tools.forms.InvoiceLineForm',
                'related_name': 'lines',
                'field': 'invoice',
                'sortable': True,
                'tva_fields': ['tva'],
                'show_list': [
                    ('label', _(u'Titre')),
                    ('quantity', _(u'Quantité')),
                    ('value', _(u'Montant (HT)')),
                    ('get_tva', _(u'TVA')),
                    ('total', _(u'Montant (TTC)')),
                ]},
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class InvoiceLine(ModelUsedAsLine):

    invoice = models.ForeignKey('Invoice', related_name="lines")

    label = models.CharField(_(u'Titre'), max_length=255)
    quantity = models.DecimalField(_(u'Quantité'), max_digits=20, decimal_places=0, default=1)
    value = models.DecimalField(_('Montant (HT)'), max_digits=20, decimal_places=2)
    tva = models.DecimalField(_('TVA'), max_digits=20, decimal_places=2)

    def __unicode__(self):
        return u'%s: %s * %s + %s%%' % (self.label, self.quantity, self.value, self.tva)

    def total(self):
        return float(self.quantity) * (float(self.value) + (float(self.value) * float(self.tva) / 100.0))

    def get_tva(self):
        from accounting_core.models import TVA
        return TVA.tva_format(self.tva)


class _InternalTransfer(GenericModel, GenericStateModel, GenericTaggableObject, AccountingYearLinked, AgepolyEditableModel, GenericGroupsModel, GenericContactableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'

    name = models.CharField(_('Raison du transfert'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    account = FalseFK('accounting_core.models.Account', verbose_name=_(u'Compte concerné'))
    cost_center_from = FalseFK('accounting_core.models.CostCenter', related_name='internal_transfer_from', verbose_name=_(u'Centre de coûts prélevé'))
    cost_center_to = FalseFK('accounting_core.models.CostCenter', related_name='internal_transfer_to', verbose_name=_(u'Centre de coûts versé'))
    amount = models.DecimalField(_('Montant'), max_digits=20, decimal_places=2)

    class MetaData:
        list_display = [
            ('name', _('Raison')),
            ('account', _('Compte')),
            ('amount', _('Montant')),
            ('cost_center_from', _(u'De')),
            ('cost_center_to', _(u'Vers')),
            ('status', _('Statut')),
        ]

        details_display = list_display + [('description', _(u'Description')), ('accounting_year', _(u'Année comptable')), ]
        filter_fields = ('name', 'status', 'account__name', 'account__account_number', 'amount', 'cost_center_from__name', 'cost_center_from__account_number', 'cost_center_to__name', 'cost_center_to__account_number')

        base_title = _(u'Transferts internes')
        list_title = _(u'Liste des transferts internes')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-exchange'

        menu_id = 'menu-compta-transfert'

        help_list = _(u"""Les transferts internes permettent de déplacer de l'argent entre les entitées de l'AGEPoly sur un même compte.

Ils peuvent être utilisés dans le cadre d'une commande groupée ou d'un remboursement d'une unité vers l'autre.""")

    class Meta:
        abstract = True

    class MetaGroups(GenericGroupsModel.MetaGroups):
        pass

    class MetaState:
        states = {
            '0_draft': _('Brouillon'),
            '1_agep_validable': _(u'Attente accord AGEPoly'),
            '2_accountable': _(u'A comptabiliser'),
            '3_archived': _(u'Archivé'),
            '3_canceled': _(u'Annulé'),
        }
        default = '0_draft'

        states_texts = {
            '0_draft': _(u'L\'objet est en cours de création.'),
            '1_agep_validable': _(u'L\'objet doit être accepté par l\'AGEPoly.'),
            '2_accountable': _(u'L\'objet est en attente d\'être comptabilisé.'),
            '3_archived': _(u'L\'objet est archivé. Il n\'est plus modifiable.'),
            '3_canceled': _(u'L\'objet a été annulé.'),
        }

        states_links = {
            '0_draft': ['1_agep_validable', '3_canceled'],
            '1_agep_validable': ['2_accountable', '3_canceled'],
            '2_accountable': ['3_archived', '3_canceled'],
            '3_archived': [],
            '3_canceled': [],
        }

        list_quick_switch = {
            '0_draft': [('1_agep_validable', 'fa fa-question', _(u'Demander accord AGEPoly')), ('3_canceled', 'fa fa-ban', _(u'Annuler')), ],
            '1_agep_validable': [('2_accountable', 'fa fa-check', _(u'Demander à comptabiliser')), ('3_canceled', 'fa fa-ban', _(u'Annuler'))],
            '2_accountable': [('3_archived', 'glyphicon glyphicon-remove-circle', _(u'Archiver')), ('3_canceled', 'fa fa-ban', _(u'Annuler'))],
        }

        states_colors = {
            '0_draft': 'primary',
            '1_agep_validable': 'default',
            '2_accountable': 'info',
            '3_archived': 'success',
            '3_canceled': 'danger',
        }

        states_icons = {
            '0_draft': '',
            '1_agep_validable': '',
            '2_accountable': '',
            '3_archived': '',
            '3_canceled': '',
        }

        states_default_filter = '0_draft,1_agep_validable'
        status_col_id = 4

    def may_switch_to(self, user, dest_state):
        if self.status[0] == '3' and not user.is_superuser:
            return False

        if dest_state == '3_canceled' and self.rights_can('EDIT', user):
            return True

        return super(_InternalTransfer, self).may_switch_to(user, dest_state)

    def can_switch_to(self, user, dest_state):

        if self.status[0] == '3' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé/annulé'))

        if dest_state == '3_canceled' and self.rights_can('EDIT', user):
            return (True, None)

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits.'))

        return super(_InternalTransfer, self).can_switch_to(user, dest_state)

    def rights_can_SHOW(self, user):
        if self.rights_in_unit(user, self.cost_center_from.unit, access='TRESORERIE') or self.rights_in_unit(user, self.cost_center_to.unit, access='TRESORERIE'):
            return True

        return super(_InternalTransfer, self).rights_can_SHOW(user)

    def rights_can_LIST(self, user):
        return super(_InternalTransfer, self).rights_can_SHOW(user)

    def rights_can_DISPLAY_LOG(self, user):
        return self.rights_can_SHOW(user)

    def rights_can_EDIT(self, user):
        if self.status[0] == '3':
            return False

        return super(_InternalTransfer, self).rights_can_EDIT(user)

    def switch_status_signal(self, request, old_status, dest_status):

        s = super(_InternalTransfer, self)

        if hasattr(s, 'switch_status_signal'):
            s.switch_status_signal(request, old_status, dest_status)

        if dest_status == '1_agep_validable':
            notify_people(request, '%s.validable' % (self.__class__.__name__,), 'internaltransfer_validable', self, self.people_in_root_unit('TRESORERIE'))
        elif dest_status == '2_accountable':
            unotify_people('%s.validable' % (self.__class__.__name__,), self)
            notify_people(request, '%s.accountable' % (self.__class__.__name__,), 'internaltransfer_accountable', self, self.people_in_root_unit('SECRETARIAT'))
        elif dest_status[0] == '3':
            unotify_people('%s.accountable' % (self.__class__.__name__,), self)
            tresoriers = self.people_in_unit(self.cost_center_from.unit, 'TRESORERIE', no_parent=True) + self.people_in_unit(self.cost_center_to.unit, 'TRESORERIE', no_parent=True)
            notify_people(request, '%s.accepted' % (self.__class__.__name__,), 'internaltransfer_accepted', self, list(set(tresoriers + self.build_group_members_for_editors())))

    def __unicode__(self):
        return u"{} ({})".format(self.name, self.accounting_year)

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        """Set querysets according to the selected accounting_year"""
        from accounting_core.models import Account, CostCenter

        form.fields['account'].queryset = Account.objects.filter(accounting_year=self.accounting_year).order_by('category__order')
        form.fields['cost_center_from'].queryset = CostCenter.objects.filter(accounting_year=self.accounting_year).order_by('account_number')
        form.fields['cost_center_to'].queryset = CostCenter.objects.filter(accounting_year=self.accounting_year).order_by('account_number')

    def genericFormExtraClean(self, data, form):
        if data['cost_center_from'] == data['cost_center_to']:
            raise forms.ValidationError(_(u'Les deux centres de coûts doivent être différents.'))
