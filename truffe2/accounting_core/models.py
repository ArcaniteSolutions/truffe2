# -*- coding: utf-8 -*-

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _


from generic.models import GenericModel, GenericStateModel, FalseFK, GenericGroupsModel, SearchableModel
from rights.utils import AgepolyEditableModel
from accounting_core.utils import AccountingYearLinked
from app.utils import get_current_year


class _AccountingYear(GenericModel, GenericStateModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['TRESORERIE']

    name = models.CharField(_('Nom'), max_length=255, unique=True)
    start_date = models.DateTimeField(_(u'Date de début'), blank=True, null=True)
    end_date = models.DateTimeField(_('Date de fin'), blank=True, null=True)
    subvention_deadline = models.DateTimeField(_(u'Délai pour les subventions'), blank=True, null=True)
    last_accounting_import = models.DateTimeField(_(u'Dernier import de la compta'), blank=True, null=True)

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

        forced_pos = {
            '0_preparing': (0.1, 0.5),
            '1_active': (0.36, 0.5),
            '2_closing': (0.62, 0.5),
            '3_archived': (0.9, 0.5),
        }

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u""

        fields = [
            'name',
        ]

    def may_switch_to(self, user, dest_state):

        return super(_AccountingYear, self).rights_can_EDIT(user)

    def can_switch_to(self, user, dest_state):

        if self.status == '3_archived' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if int(dest_state[0]) - int(self.status[0]) != 1 and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sauter des étapes ou revenir en arrière.'))

        if not super(_AccountingYear, self).rights_can_EDIT(user):
            return (False, _('Pas les droits.'))

        return super(_AccountingYear, self).can_switch_to(user, dest_state)

    class MetaEdit:
        datetime_fields = ['start_date', 'end_date', 'subvention_deadline']

        only_if = {
            'last_accounting_import': lambda _: False
        }

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def rights_can_EDIT(self, user):
        # On ne peut éditer que les années en préparation ou active
        if self.status in ['0_preparing', '1_active']:
            return super(_AccountingYear, self).rights_can_EDIT(user)
        return False

    def rights_can_DELETE(self, user):
        # On ne peut supprimer que les années en préparation
        if self.status == '0_preparing':
            return super(_AccountingYear, self).rights_can_DELETE(user)
        return False

    @classmethod
    def build_year_menu(cls, mode, user):

        retour = []

        retour += list(cls.objects.filter(status='1_active', deleted=False).order_by('-end_date'))
        retour += list(cls.objects.filter(status='2_closing', deleted=False).order_by('-end_date'))

        # On peut sélectionner les années en préparation que si on est
        # trésorie du comité agepoly ou super_user
        if user.is_superuser or cls().rights_in_root_unit(user, 'TRESORERIE'):
            retour += list(cls.objects.filter(status='0_preparing', deleted=False).order_by('-end_date'))

        # On peut sélectionner les années archivée qu'en list (sauf si on est
        # super_user)
        if mode == 'LIST' or user.is_superuser:
            retour += list(cls.objects.filter(status='3_archived', deleted=False).order_by('-end_date'))

        return retour


class _CostCenter(GenericModel, AccountingYearLinked, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['TRESORERIE', 'SECRETARIAT']

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

        default_sort = "[1, 'asc']"  # account_number

        details_display = list_display + [('description', _(u'Description')), ('accounting_year', _(u'Année comptable'))]
        filter_fields = ('name', 'account_number', 'unit__name')

        base_title = _(u'Centres de coût')
        list_title = _(u'Liste des centres de coût')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-suitcase'

        menu_id = 'menu-compta-centrecouts'

        help_list = _(u"""Les centres de coût sont les différents comptes qui appartiennent aux unités de l'AGEPoly (commissions, équipes, sous-commissions, Comité de Direction).""")

    class MetaAccounting:
        copiable = True

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u"centre cout"

        fields = [
            'name',
            'account_number',
            'description',
        ]

    def __unicode__(self):
        return u"{} - {}".format(self.account_number, self.name)

    def genericFormExtraClean(self, data, form):
        """Check that unique_together is fulfiled"""
        from accounting_core.models import CostCenter

        if CostCenter.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), name=data['name']).count():
            raise forms.ValidationError(_(u'Un centre de coûts avec ce nom existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

        if CostCenter.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), account_number=data['account_number']).count():
            raise forms.ValidationError(_(u'Un centre de coûts avec ce numéro de compte existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées


class _AccountCategory(GenericModel, AccountingYearLinked, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['TRESORERIE', 'SECRETARIAT']

    name = models.CharField(_(u'Nom de la catégorie'), max_length=255)
    parent_hierarchique = models.ForeignKey('AccountCategory', null=True, blank=True, help_text=_(u'Catégorie parente pour la hiérarchie'))
    order = models.SmallIntegerField(_(u'Ordre dans le plan comptable'), default=0, help_text=_(u'Le plus petit d\'abord'))
    description = models.TextField(_('Description'), blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = ("name", "accounting_year")

    class MetaData:
        list_display = [
            ('name', _(u'Nom de la catégorie')),
            ('parent_hierarchique', _(u'Catégorie parente'))
        ]

        details_display = list_display + [('accounting_year', _(u'Année Comptable')), ('description', _(u'Description'))]

        default_sort = "[3, 'asc']"  # pk -> order
        trans_sort = {'pk': 'order'}

        filter_fields = ('name',)

        base_title = _(u'Catégories des comptes de CG')
        list_title = _(u'Liste des catégories')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-folder-open'

        menu_id = 'menu-compta-categoriescompteCG'

        help_list = _(u"""Les catégories des comptes de comptabilité générale servent à classer les comptes de CG dans les différents documents comptables.""")

    class MetaAccounting:
        copiable = True
        foreign = (('parent_hierarchique', 'AccountCategory'),)

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u""

        fields = [
            'name',
            'description',
        ]

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

        if data['parent_hierarchique'] and data['parent_hierarchique'].accounting_year != get_current_year(form.truffe_request):
            raise forms.ValidationError(_(u'La catégorie parente choisie n\'appartient pas à la bonne année comptable.'))

    def get_children_categories(self):
        """Return the categories whose parent is self."""
        return self.accountcategory_set.order_by('order', 'name')

    def get_root_parent(self):
        """Return the category at the root level"""
        if self.parent_hierarchique:
            return self.parent_hierarchique.get_root_parent()
        else:
            return self

    def get_accounts(self):
        """Return the list of accounts whose category is self ordered by account number."""
        return self.account_set.order_by('account_number')


class _Account(GenericModel, AccountingYearLinked, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['TRESORERIE', 'SECRETARIAT']

    VISIBILITY_CHOICES = (
        ('all', _(u'Visible à tous')),
        ('cdd', _(u'Visible au Comité de Direction uniquement')),
        ('root', _(u'Visible aux personnes qui gère la comptabilité générale')),
        ('none', _(u'Visible à personne')),
    )

    name = models.CharField(_('Nom du compte'), max_length=255)
    account_number = models.CharField(_(u'Numéro du compte'), max_length=10)
    visibility = models.CharField(_(u'Visibilité dans les documents comptables'), max_length=50, choices=VISIBILITY_CHOICES)
    category = FalseFK('accounting_core.models.AccountCategory', verbose_name=_(u'Catégorie'))
    description = models.TextField(_('Description'), blank=True, null=True)

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
        filter_fields = ('name', 'account_number', 'category__name')

        base_title = _(u'Comptes de Comptabilité Générale')
        list_title = _(u'Liste des comptes')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-money'

        menu_id = 'menu-compta-comptesCG'

        help_list = _(u"""Les comptes de comptabilité générale sont les différents comptes qui apparaissent dans la comptabilité de l'AGEPoly.
Ils permettent de séparer les recettes et les dépenses par catégories.""")

    class MetaAccounting:
        copiable = True
        foreign = (('category', 'AccountCategory'),)

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u""

        fields = [
            'name',
            'description',
            'account_number',
            'category',
        ]

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
        """Check that unique_together is fulfiled and that category is in the right accounting_year"""
        from accounting_core.models import Account

        if Account.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), name=data['name']).count():
            raise forms.ValidationError(_(u'Un compte de CG avec ce nom existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

        if Account.objects.exclude(pk=self.pk).filter(accounting_year=get_current_year(form.truffe_request), account_number=data['account_number']).count():
            raise forms.ValidationError(_(u'Un compte de CG avec ce numéro de compte existe déjà pour cette année comptable.'))  # Potentiellement parmi les supprimées

        if data['category'].accounting_year != get_current_year(form.truffe_request):
            raise forms.ValidationError(_(u'La catégorie choisie n\'appartient pas à la bonne année comptable.'))

    def rights_can_SHOW(self, user):

        if not self.pk:
            return super(_Account, self).rights_can_SHOW(user)
        elif self.visibility == 'none':
            return user.is_superuser
        elif self.visibility == 'root':
            return self.rights_in_root_unit(user, 'TRESORERIE')
        elif self.visibility == 'cdd':
            return user in self.people_in_root_unit()
        elif self.visibility == 'all':
            return not user.is_external()


class _TVA(GenericModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['TRESORERIE', 'SECRETARIAT']

    name = models.CharField(_(u'Nom de la TVA'), max_length=255)
    value = models.DecimalField(_('Valeur (%)'), max_digits=20, decimal_places=2)
    agepoly_only = models.BooleanField(_(u'Limiter l\'usage au comité de l\'AGEPoly'), default=False)
    account = models.ForeignKey('accounting_core.Account', verbose_name=_('Compte de TVA'))
    code = models.CharField(verbose_name=_('Code de TVA'), max_length=255)


    class Meta:
        abstract = True

    class MetaData:
        list_display = [
            ('name', _(u'Nom')),
            ('value', _(u'Valeur (%)')),
            ('agepoly_only', _(u'Limité AGEPoly ?')),
        ]

        default_sort = "[1, 'asc']"  # name

        details_display = list_display
        filter_fields = ('name', 'value',)

        base_title = _(u'TVA')
        list_title = _(u'Liste des taux de TVA')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-filter'

        menu_id = 'menu-compta-tva'

        yes_or_no_fields = ['agepoly_only',]

        help_list = _(u"""Les TVA sélectionnables dans les champs de TVA. Il est possible de restrainre l'usage de certaines TVA au CDD.

Les TVA ne sont pas liées aux autres objets comptables, il est possible de les modifier à tout moment sans risques.""")

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u""

        fields = [
            'name',
            'value',
        ]

    def __init__(self, *args, **kwargs):
        super(_TVA, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'ANYTVA': _(u'Peut utiliser n\'importe quelle valeure de TVA.'),
        })

    def __unicode__(self):
        return u"{}% ({})".format(self.value, self.name)

    def rights_can_ANYTVA(self, user):
        return self.rights_in_root_unit(user, 'TRESORERIE')

    @staticmethod
    def tva_format(tva):

        from accounting_core.models import TVA

        try:
            tva_object = TVA.objects.get(value=tva)
        except:
            tva_object = None

        return u'{}% ({})'.format(tva, tva_object.name if tva_object else u'TVA Spéciale')


class AccountingGroupModels(object):

    class MetaGroups(GenericGroupsModel.MetaGroups):
        pass

    def __init__(self, *args, **kwargs):

        super(AccountingGroupModels, self).__init__(*args, **kwargs)

        self.MetaGroups = type("MetaGroups", (self.MetaGroups,), {})
        self.MetaGroups.groups_update({
            'agep_compta': _(u'L\'administrateur de l\'AGEPoly'),
            'agep_secretaire': _(u'Les secrétaires de l\'AGEPoly'),
            'unit_compta': _(u'Le trésorier de l\'unité liée'),
            'compta_everyone': _(u'Toutes les personnes liées via la compta (Admin et secrétaires AGEP, trésorier unité, éditeurs de l\'objet)'),
        })

    def build_group_members_for_agep_compta(self):
        return self.people_in_root_unit('TRESORERIE')

    def build_group_members_for_agep_secretaire(self):
        return self.people_in_root_unit('SECRETARIAT')

    def build_group_members_for_unit_compta(self):
        return self.people_in_linked_unit('TRESORERIE')

    def build_group_members_for_compta_everyone(self):

        retour = []

        def _do(f):
            for user in f():
                if user not in retour:
                    retour.append(user)

        map(_do, [self.build_group_members_for_agep_compta, self.build_group_members_for_agep_secretaire, self.build_group_members_for_unit_compta, self.build_group_members_for_editors])

        return retour
