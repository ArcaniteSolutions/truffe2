# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from generic.models import GenericModel, FalseFK
from rights.utils import AgepolyEditableModel, UnitEditableModel
from users.models import TruffeUser

import datetime
from multiselectfield import MultiSelectField


class _Unit(GenericModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'INFORMATIQUE'
        world_ro_access = True

    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=64, blank=True, null=True, help_text=_(u'Utilisé pour la synchronisation des accréditations'))
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    is_commission = models.BooleanField(default=False, help_text=_(u'Cocher si cette unité est une commission de l\'AGEPoly'))
    is_equipe = models.BooleanField(default=False, help_text=_(u'Cocher si cette unité est une équipe de l\'AGEPoly'))
    is_hidden = models.BooleanField(default=False, help_text=_(u'Cocher rend l\'unité inselectionnable au niveau du contexte d\'unité, sauf pour les administrateurs et les personnes accréditées comité de l\'AGEPoly'))

    parent_hierarchique = models.ForeignKey('Unit', blank=True, null=True, help_text=_(u'Pour les commissions et les équipes, sélectionner le comité de l\'AGEPoly. Pour les sous-commisions, sélectionner la commission parente. Pour un coaching de section, sélectionner la commission Coaching. Pour le comité de l\'AGEPoly, ne rien mettre.'))

    class MetaData:
        list_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('is_hidden', _(u'Cachée ?')),
            ('parent_hierarchique', _('Parent')),
            ('president', _(u'Président'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('is_hidden', _(u'Cachée ?')),
            ('parent_hierarchique', _('Parent')),
            ('president', _(u'Président')),
            ('id_epfl', _('ID EPFL')),
            ('description', _('Description')),
            ('url', _('URL')),
        ]

        default_sort = "[1, 'asc']"  # name

        yes_or_no_fields = ['is_commission', 'is_equipe', 'is_hidden']

        filter_fields = ('name', )

        base_title = _(u'Unités')
        list_title = _(u'Liste de toutes les unités')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

        menu_id = 'menu-units-units'

        help_list = _(u"""Les unités sont les différents groupes de l'AGEPoly (Comité de l'AGEPoly, commissions, équipes, etc.)

Les unités sont organisées en arbre hiérarchique, avec le Comité de l'AGEPoly au sommet.""")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def genericFormExtraInit(self, form, current_user, *args, **kwargs):
        """Update queryset for parent_hierarchique"""
        if 'parent_hierarchique' in form.fields:
            from units.models import Unit
            form.fields['parent_hierarchique'].queryset = Unit.objects.order_by('name')

    def rights_can_select(self):
        """Return true if the unit can be selected in the selector menu"""
        return True

    _rights_can_select = lambda unit: True

    def set_rights_can_select(self, f):
        def __tmp():
            return f(self)
        self.rights_can_select = __tmp
        self._rights_can_select = f

    def rights_can_edit(self):
        """Return true if the user has edit right"""
        return True

    _rights_can_edit = lambda unit: True

    def set_rights_can_edit(self, f):
        def __tmp():
            return f(self)
        self.rights_can_edit = __tmp
        self._rights_can_edit = f

    _can_use_hidden = False  # Internal property

    def check_if_can_use_hidden(self, user):
        self._can_use_hidden = user.is_superuser or self.rights_in_root_unit(user)

        return self._can_use_hidden

    def has_sub(self):
        """Return true if the unit has subunits"""
        liste = self.unit_set.filter(deleted=False)

        if not self._can_use_hidden:
            liste = liste.filter(is_hidden=False)

        return liste.count() > 0

    def only_one_sub_type(self):
        tt = 0

        if self.sub_com():
            tt += 1
        if self.sub_eqi():
            tt += 1
        if self.sub_grp():
            tt += 1

        return tt == 1

    def sub_com(self):
        """Return the sub units, but only commissions"""
        retour = []

        liste = self.unit_set.filter(is_commission=True, deleted=False)

        if not self._can_use_hidden:
            liste = liste.filter(is_hidden=False)

        for unit in liste.order_by('name'):
            unit.set_rights_can_select(self._rights_can_select)
            unit.set_rights_can_edit(self._rights_can_edit)
            unit._can_use_hidden = self._can_use_hidden
            retour.append(unit)
        return retour

    def sub_eqi(self):
        """Return the sub units, but only groups"""
        retour = []

        liste = self.unit_set.exclude(is_commission=True).filter(is_equipe=True, deleted=False)

        if not self._can_use_hidden:
            liste = liste.filter(is_hidden=False)

        for unit in liste.order_by('name'):
            unit.set_rights_can_select(self._rights_can_select)
            unit.set_rights_can_edit(self._rights_can_edit)
            unit._can_use_hidden = self._can_use_hidden
            retour.append(unit)
        return retour

    def sub_grp(self):
        """Return the sub units, without groups or commissions"""
        retour = []

        liste = self.unit_set.filter(is_commission=False, is_equipe=False, deleted=False)

        if not self._can_use_hidden:
            liste = liste.filter(is_hidden=False)

        for unit in liste.order_by('name'):
            unit.set_rights_can_select(self._rights_can_select)
            unit.set_rights_can_edit(self._rights_can_edit)
            unit._can_use_hidden = self._can_use_hidden
            retour.append(unit)
        return retour

    def is_user_in_groupe(self, user, access=None, parent_mode=False, no_parent=False):
        for accreditation in self.accreditation_set.filter(user=user, end_date=None):

            if accreditation.is_valid():

                # No acces: Only an accred is needed
                if not access:
                    return True

                # If role has acces, ok
                if accreditation.role.access:
                    if type(access) is list:
                        for acc in access:
                            if acc in accreditation.role.access:
                                return True
                        return False

                    if access in accreditation.role.access:
                        return True

                # Check valid delegations for this accred
                access_delegations = self.accessdelegation_set.filter((Q(user=user) | Q(user=None)) & (Q(role=accreditation.role) | Q(role=None))).all()

                for access_delegation in access_delegations:
                    if not parent_mode or access_delegation.valid_for_sub_units:
                        if type(access) is list:
                            for acc in access:
                                if acc in access_delegation.access:
                                    return True
                            return False

                        if access in access_delegation.access:
                            return True

        if self.parent_hierarchique and not no_parent:
            return self.parent_hierarchique.is_user_in_groupe(user, access, True)
        return False

    def users_with_access(self, access=None, no_parent=False):

        retour = []

        for accreditation in self.accreditation_set.filter(end_date=None):
            if not accreditation.is_valid():
                continue

            if accreditation.user in retour:
                continue

            if not access or self.is_user_in_groupe(accreditation.user, access, no_parent=no_parent):  # To avoid duplicate code, check if access with other function
                retour.append(accreditation.user)

        return retour

    @property
    def president(self):
        return ', '.join([u.user.get_full_name() for u in list(self.accreditation_set.filter(end_date=None, role__pk=settings.PRESIDENT_ROLE_PK, hidden_in_truffe=False))])

    def can_delete(self):

        if self.accreditation_set.count():
            return (False, _(u'Au moins une accéditation existe avec cette unité, impossible de supprimer l\'unité (NB: Historique compris).'))

        return (True, None)

    def current_accreds(self):
        return self.accreditation_set.filter(end_date=None).order_by('role__ordre', 'user__first_name', 'user__last_name')

    def get_users(self):
        return [a.user for a in self.current_accreds()]

    def rights_can_SHOW(self, user):
        if self.is_hidden and not self.check_if_can_use_hidden(user):
            return False

        return super(_Unit, self).rights_can_SHOW(user)


class _Role(GenericModel, AgepolyEditableModel):
    """Un role, pour une accred"""

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'INFORMATIQUE'
        world_ro_access = True

    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=255, null=True, blank=True, help_text=_(u'Mettre ici l\'ID accred du rôle pour la synchronisation EPFL'))
    description = models.TextField(null=True, blank=True)
    ordre = models.IntegerField(null=True, blank=True, help_text=_(u'Il n\'est pas possible d\'accréditer la même personne dans la même unité plusieurs fois. Le rôle avec le plus PETIT ordre sera pris en compte'))

    need_validation = models.BooleanField(_(u'Nécessite validation'), default=False, help_text=_(u'A cocher pour indiquer que le comité de l\'AGEPoly doit valider l\'attribution du rôle'))

    ACCESS_CHOICES = (
        ('PRESIDENCE', _(u'Présidence')),
        ('TRESORERIE', _(u'Trésorerie')),
        ('COMMUNICATION', _('Communication')),
        ('INFORMATIQUE', _('Informatique')),
        ('ACCREDITATION', _(u'Accréditations')),
        ('LOGISTIQUE', _('Logistique')),
        ('SECRETARIAT', _(u'Secrétariat')),
        ('COMMISSIONS', _(u'Commissions'))
    )

    access = MultiSelectField(choices=ACCESS_CHOICES, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def get_access(self):
        if self.access:
            return u', '.join(list(self.access))

    class MetaData:
        list_display = [
            ('name', _('Nom')),
            ('id_epfl', _('ID EPFL ?')),
            ('need_validation', _('Validation ?')),
            ('ordre', _('Ordre'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('description', _('Description')),
            ('id_epfl', _('ID EPFL ?')),
            ('need_validation', _('Validation ?')),
            ('ordre', _('Ordre')),
            ('get_access', _(u'Accès')),
        ]

        default_sort = "[1, 'asc']"  # name

        filter_fields = ('name', 'id_epfl', 'description')

        yes_or_no_fields = ['need_validation']

        base_title = _(u'Rôles')
        list_title = _(u'Liste de tous les rôles')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

        menu_id = 'menu-units-roles'

        help_list = _(u"""Les rôles sont les différents type d'accréditations possibles pour une unité.

Certains rôles donnent des accès particuliers.
Par exemple, le rôle 'Trésorier' donne l'accès TRÉSORERIE. Les droits sont gérés en fonction des accès !""")

    class Meta:
        abstract = True

    def can_delete(self):

        if self.accreditation_set.count():
            return (False, _(u'Au moins une accréditation existe avec ce rôle, impossible de supprimer le rôle (NB: Historique compris)'))

        return (True, None)


class Accreditation(models.Model, UnitEditableModel):
    unit = models.ForeignKey('Unit')
    user = models.ForeignKey(TruffeUser)
    role = models.ForeignKey('Role')

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    renewal_date = models.DateTimeField(auto_now_add=True)

    display_name = models.CharField(_(u'Titre'), max_length=255, blank=True, null=True, help_text=_(u'Précision optionnelle à afficher dans Truffe. Peut être utilisé pour préciser la fonction, par exemple: "Responsable Réseau" pour une accréditation de Responsable Informatique.'))

    no_epfl_sync = models.BooleanField(_(u'Désactiver syncronisation EPFL'), default=False, help_text=_(u'A cocher pour ne pas synchroniser cette accréditation au niveau EPFL'))
    hidden_in_epfl = models.BooleanField(_(u'Cacher au niveau EPFL'), default=False, help_text=_(u'A cocher pour ne pas rendre public l\'accréditation au niveau EPFL'))
    hidden_in_truffe = models.BooleanField(_(u'Cacher dans Truffe'), default=False, help_text=_(u'A cocher pour ne pas rendre public l\'accréditation au niveau truffe (sauf aux accréditeurs sur la page d\'accréditation)'))

    need_validation = models.BooleanField(default=False)

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        unit_ro_access = True
        access = 'ACCREDITATION'

    class MetaRights(UnitEditableModel.MetaRights):
        linked_unit_property = 'unit'

    def __init__(self, *args, **kwargs):
        super(Accreditation, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'INGORE_PREZ': _(u'Peut supprimer le dernier président'),
            'VALIDATE': _(u'Valider les changements'),
        })

    def exp_date(self):
        """Returne la date d'expiration de l'accred"""
        return self.renewal_date + datetime.timedelta(days=365)

    def is_valid(self):
        """Returne true si l'accred est valide"""
        return self.end_date is None

    def get_role_or_display_name(self):
        if self.display_name:
            return u'%s (%s)' % (self.role, self.display_name)
        return u'%s' % (self.role,)

    def rights_can_INGORE_PREZ(self, user):
        return self.rights_in_root_unit(user, self.MetaRightsUnit.access)

    def rights_can_VALIDATE(self, user):
        return self.rights_in_root_unit(user, self.MetaRightsUnit.access)

    def rights_can_SHOW(self, user):
        if self.hidden_in_truffe:
            return self.rights_in_root_unit(user, self.MetaRightsUnit.access) and super(Accreditation, self).rights_can_SHOW(user)
        else:
            return super(Accreditation, self).rights_can_SHOW(user)

    def check_if_validation_needed(self, request):

        if not self.role.need_validation:
            return

        if self.rights_can('VALIDATE', request.user):
            return

        if not self.unit.is_commission:  # Seulement pour les commisions !
            return

        self.need_validation = True

        from notifications.utils import notify_people
        dest_users = self.people_in_root_unit('ACCREDITATION')

        for user in self.people_in_root_unit('COMMISSIONS'):
            if user not in dest_users:
                dest_users.append(user)

        notify_people(request, 'Accreds.ToValidate', 'accreds_tovalidate', self, dest_users)

    def __unicode__(self):
        return '%s (%s)' % (self.user, self.get_role_or_display_name())

    def display_url(self):
        return '%s?upk=%s' % (reverse('units.views.accreds_list'), self.unit.pk,)


class AccreditationLog(models.Model):

    accreditation = models.ForeignKey(Accreditation)
    who = models.ForeignKey(TruffeUser)
    when = models.DateTimeField(auto_now_add=True)
    what = models.TextField(blank=True, null=True)

    TYPE_CHOICES = [
        ('created', _(u'Créée')),
        ('edited', _(u'Modifiée')),
        ('deleted', _(u'Supprimée')),
        ('autodeleted', _(u'Supprimée automatiquement')),
        ('renewed', _(u'Renouvelée')),
        ('validated', _(u'Validée')),
    ]

    type = models.CharField(max_length=32, choices=TYPE_CHOICES)


class _AccessDelegation(GenericModel, UnitEditableModel):
    unit = FalseFK('units.models.Unit')

    access = MultiSelectField(choices=_Role.ACCESS_CHOICES, blank=True, null=True)
    valid_for_sub_units = models.BooleanField(_(u'Valide pour les sous-unités'), default=False, help_text=_(u'Si sélectionné, les accès supplémentaires dans l\'unité courante seront aussi valides dans les sous-unités'))

    user = models.ForeignKey(TruffeUser, blank=True, null=True, help_text=_(u'(Optionnel !) L\'utilisateur concerné. L\'utilisateur doit disposer d\'une accréditation dans l\'unité.'))
    role = FalseFK('units.models.Role', blank=True, null=True, help_text=_(u'(Optionnel !) Le rôle concerné.'))

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        unit_ro_access = True
        access = 'ACCREDITATION'

    class MetaData:
        list_display = [
            ('get_display_list', ''),
            ('user', _('Utilisateur')),
            ('role', _(u'Rôle')),
            ('get_access', _(u'Accès'))
        ]

        details_display = [
            ('user', _('Utilisateur')),
            ('role', _('Rôle')),
            ('get_access', _(u'Accès supplémentaires')),
            ('valid_for_sub_units', _(u'Valide pour les sous-unités'))
        ]

        default_sort = "[0, 'asc']"  # id

        filter_fields = ()
        not_sortable_colums = ['get_display_list', ]

        base_title = _(u'Délégation d\'accès')
        list_title = _(u'Liste de toutes les délégations d\'accès')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

        menu_id = 'menu-units-delegations'

        yes_or_no_fields = ['valid_for_sub_units']

        has_unit = True

        help_list = _(u"""Les délégations d'accès permettent de donner des accès supplémentaires dans une unité.

Les accès sont normalement déterminés en fonction des accréditations, au niveau global.
Par exemple, une personne accréditée en temps que 'Trésorier' dans une unité disposera de l'accès TRESORERIE pour l'unité.

Avec les délégations d'accês, il est par exemple possible de donner l'accès "COMMUNICATION" à tout les membres d'une unité en créant une délégations d'accès.

Il est aussi possible de restreindre une délégation â un utilisateur ou à un rôle particulier.""")

    class Meta:
        abstract = True

    def get_access(self):
        if self.access:
            return u', '.join(list(self.access))

    def __unicode__(self):
        return _(u'Accês supplémentaire n°%s' % (self.pk,))

    def delete_signal(self, request):
        self.save_signal()

    def save_signal(self):
        """Cleanup rights"""

        for user in self.unit.get_users():
            user.clear_rights_cache()

    def get_display_list(self):
        return _(u'Délégation #{}'.format(self.pk))
