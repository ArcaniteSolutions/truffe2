# -*- coding: utf-8 -*-

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _


from generic.models import GenericModel, GenericStateModel, FalseFK
from rights.utils import AgepolyEditableModel
from accounting_core.utils import AccountingYearLinked
from app.utils import get_current_year


class _AccountingYear(GenericModel, GenericStateModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'
        world_ro_access = True

    name = models.CharField(_('Nom'), max_length=255, unique=True)
    start_date = models.DateTimeField(_(u'Date de début'), blank=True, null=True)
    end_date = models.DateTimeField(_('Date de fin'), blank=True, null=True)
    subvention_deadline = models.DateTimeField(_(u'Délai pour les subventions'), blank=True, null=True)

    class MetaData:
        list_display = [
            ('name', _(u'Nom de l\'année comptable')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]
        details_display = list_display
        details_display.insert(3, ('subvention_deadline', _(u'Délai pour les subventions')))

        default_sort = "[1, 'asc']"  # name

        filter_fields = ('name', 'status')

        base_title = _(u'Années Comptables')
        list_title = _(u'Liste des années comptables')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-calendar-o'

        menu_id = 'menu-compta-anneecomptable'

        datetime_fields = ['start_date', 'end_date', 'subvention_deadline']

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
        datetime_fields = ['start_date', 'end_date', 'subvention_deadline']

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


class _CostCenter(GenericModel, AccountingYearLinked, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'
        world_ro_access = True

    name = models.CharField(_(u'Nom du centre de coût'), max_length=255)
    account_number = models.CharField(_(u'Numéro associé au centre de coût'), max_length=10)
    unit = FalseFK('units.models.Unit', verbose_name=_(u'Appartient à'))
    description = models.TextField(_('Description'), blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = (("name", "accounting_year"), ("account_number", "accounting_year"))

    class MetaData:
        list_display = [
            ('account_number', _(u'Numéro')),
            ('name', _(u'Nom du centre de coût')),
            ('unit', _(u'Appartient à'))
        ]

        default_sort = "[2, 'asc']"  # name

        details_display = list_display + [('description', _(u'Description')), ('accounting_year', _(u'Année comptable'))]
        filter_fields = ('name', 'account_number', 'unit')

        base_title = _(u'Centres de coût')
        list_title = _(u'Liste des centres de coût')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-smile-o'

        menu_id = 'menu-compta-centrecouts'

        help_list = _(u"""Les centres de coût sont les différents comptes qui appartiennent aux unités de l'AGEPoly (commissions, équipes, sous-commissions, Comité de Direction).""")

    class MetaAccounting:
        copiable = True

    def __unicode__(self):
        return u"{} - {}".format(self.account_number, self.name)

    def genericFormExtraClean(self, data, form):
        """Check that unique_together is fulfiled"""
        from accounting_core.models import CostCenter

        if CostCenter.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), name=data['name']).count():
            raise forms.ValidationError(_(u'Un centre de coûts avec ce nom existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

        if CostCenter.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), account_number=data['account_number']).count():
            raise forms.ValidationError(_(u'Un centre de coûts avec ce numéro de compte existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées


class _AccountCategory(GenericModel, AccountingYearLinked, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'
        world_ro_access = False

    name = models.CharField(_(u'Nom de la catégorie'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    parent_hierarchique = models.ForeignKey('AccountCategory', null=True, blank=True, help_text=_(u'Catégorie parente pour la hiérarchie'))

    class Meta:
        abstract = True
        unique_together = ("name", "accounting_year")

    class MetaData:
        list_display = [
            ('name', _(u'Nom de la catégorie')),
            ('parent_hierarchique', _(u'Catégorie parente'))
        ]

        details_display = list_display + [('accounting_year', _(u'Année Comptable')), ('description', _(u'Description'))]

        default_sort = "[1, 'asc']"  # name

        filter_fields = ('name', 'parent_hierarchique')

        base_title = _(u'Catégories des comptes de CG')
        list_title = _(u'Liste des catégories')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-smile-o'

        menu_id = 'menu-compta-categoriescompteCG'

        help_list = _(u"""Les catégories des comptes de comptabilité générale servent à classer les comptes de CG dans les différents documents comptables.""")

    class MetaAccounting:
        copiable = True
        foreign = (('parent_hierarchique', 'AccountCategory'),)

    def __unicode__(self):
        return u"{} ({})".format(self.name, self.accounting_year)

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        """Reduce the list of possible parents to those on the same accounting year."""
        from accounting_core.models import AccountCategory
        form.fields['parent_hierarchique'].queryset = AccountCategory.objects.filter(accounting_year=self.accounting_year)

    def genericFormExtraClean(self, data, form):
        """Check that unique_together is fulfiled"""
        from accounting_core.models import AccountCategory

        if AccountCategory.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), name=data['name']).count():
            raise forms.ValidationError(_(u'Une catégorie avec ce nom existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

    def get_children_categories(self):
        """Return the categories whose parent is self."""
        from accounting_core.models import AccountCategory
        return AccountCategory.objects.filter(parent_hierarchique=self)


class _Account(GenericModel, AccountingYearLinked, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'TRESORERIE'
        world_ro_access = True

    VISIBILITY_CHOICES = (
        ('all', _(u'Visible à tous')),
        ('cdd', _(u'Visible au Comité de Direction uniquement')),
        ('root', _(u'Visible aux personnes qui gère la comptabilité générale')),
        ('none', _(u'Visible à personne')),
    )

    name = models.CharField(_('Nom du compte'), max_length=255)
    account_number = models.CharField(_(u'Numéro du compte'), max_length=10)
    visibility = models.CharField(_(u'Visibilité dans les documents comptables'), max_length=50, choices=VISIBILITY_CHOICES)
    description = models.TextField(_('Description'), blank=True, null=True)
    category = FalseFK('accounting_core.models.AccountCategory', verbose_name=_(u'Catégorie'))

    class Meta:
        abstract = True
        unique_together = (("name", "accounting_year"), ("account_number", "accounting_year"))

    class MetaData:
        list_display = [
            ('account_number', _(u'Numéro')),
            ('name', _('Nom du compte')),
            ('category', _(u'Catégorie'))
        ]

        default_sort = "[2, 'asc']"  # name

        details_display = list_display + [('description', _(u'Description')), ('get_visibility_display', _(u'Visibilité')), ('accounting_year', _(u'Année comptable'))]
        filter_fields = ('name', 'account_number', 'category')

        base_title = _(u'Comptes de Comptabilité Générale')
        list_title = _(u'Liste des comptes')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-smile-o'

        menu_id = 'menu-compta-comptesCG'

        help_list = _(u"""Les comptes de comptabilité générale sont les différents comptes qui apparaissent dans la comptabilité de l'AGEPoly.
Ils permettent de séparer les recettes et les dépenses par catégories.""")

    class MetaAccounting:
        copiable = True
        foreign = (('category', 'AccountCategory'),)

    def __unicode__(self):
        return u"{} - {}".format(self.account_number, self.name)

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        """Reduce the list of possible categories to the leaves of the hierarchical tree."""
        from accounting_core.models import AccountCategory

        yeared_account_categories = AccountCategory.objects.filter(accounting_year=self.accounting_year)
        yeared_account_categories = filter(lambda qs: qs.get_children_categories().count() == 0, yeared_account_categories)
        ids_yac = map(lambda yac: yac.id, yeared_account_categories)
        form.fields['category'].queryset = AccountCategory.objects.filter(id__in=ids_yac)

    def genericFormExtraClean(self, data, form):
        """Check that unique_together is fulfiled"""
        from accounting_core.models import Account

        if Account.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), name=data['name']).count():
            raise forms.ValidationError(_(u'Un compte de CG avec ce nom existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

        if Account.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), account_number=data['account_number']).count():
            raise forms.ValidationError(_(u'Un compte de CG avec ce numéro de compte existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées
