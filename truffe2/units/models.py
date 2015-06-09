# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

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

    parent_hierarchique = models.ForeignKey('Unit', blank=True, null=True, help_text=_(u'Pour les commissions et les équipes, sélectionner le comité de l\'AGEPoly. Pour les sous-commisions, sélectionner la commission parente. Pour un coaching de section, sélectionner la commission Coaching. Pour le comité de l\'AGEPoly, ne rien mettre.'))

    class MetaData:
        list_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_hierarchique', _('Parent')),
            ('president', _(u'Président'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_hierarchique', _('Parent')),
            ('president', _(u'Président')),
            ('id_epfl', _('ID EPFL')),
            ('description', _('Description')),
            ('url', _('URL')),
        ]

        yes_or_no_fields = ['is_commission', 'is_equipe']

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

    def has_sub(self):
        """Return true if the unit has subunits"""
        return self.unit_set.filter(deleted=False).order_by('name').count() > 0

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
        for unit in self.unit_set.filter(is_commission=True).filter(deleted=False).order_by('name'):
            unit.set_rights_can_select(self._rights_can_select)
            unit.set_rights_can_edit(self._rights_can_edit)
            retour.append(unit)
        return retour

    def sub_eqi(self):
        """Return the sub units, but only groups"""
        retour = []
        for unit in self.unit_set.exclude(is_commission=True).filter(is_equipe=True).filter(deleted=False).order_by('name'):
            unit.set_rights_can_select(self._rights_can_select)
            retour.append(unit)
        return retour

    def sub_grp(self):
        """Return the sub units, without groups or commissions"""
        retour = []
        for unit in self.unit_set.filter(is_commission=False).filter(is_equipe=False).filter(deleted=False).order_by('name'):
            unit.set_rights_can_select(self._rights_can_select)
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
        return ', '.join([u.user.get_full_name() for u in list(self.accreditation_set.filter(end_date=None, role__pk=settings.PRESIDENT_ROLE_PK))])

    def can_delete(self):

        if self.accreditation_set.count():
            return (False, _(u'Au moins une accéditation existe avec cette unité, impossible de supprimer l\'unité (NB: Historique compris).'))

        return (True, None)

    def current_accreds(self):
        return self.accreditation_set.filter(end_date=None).order_by('role__ordre', 'user__first_name', 'user__last_name')

    def get_users(self):
        return [a.user for a in self.current_accreds()]


class _Role(GenericModel, AgepolyEditableModel):
    """Un role, pour une accred"""

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'INFORMATIQUE'
        world_ro_access = True

    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=255, null=True, blank=True, help_text=_(u'Mettre ici l\'ID accred du rôle pour la synchronisation EPFL'))
    description = models.TextField(null=True, blank=True)
    ordre = models.IntegerField(null=True, blank=True, help_text=_(u'Il n\'est pas possible d\'accréditer la même personne dans la même unité plusieurs fois. Le rôle avec le plus PETIT ordre sera pris en compte'))

    ACCESS_CHOICES = (
        ('PRESIDENCE', _(u'Présidence')),
        ('TRESORERIE', _(u'Trésorerie')),
        ('COMMUNICATION', _('Communication')),
        ('INFORMATIQUE', _('Informatique')),
        ('LOGISTIQUE', _('Logistique')),
        ('SECRETARIAT', _(u'Secrétariat'))
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
            ('ordre', _('Ordre'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('description', _('Description')),
            ('id_epfl', _('ID EPFL ?')),
            ('ordre', _('Ordre')),
            ('get_access', _(u'Accès')),
        ]

        filter_fields = ('name', 'id_epfl', 'description')

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
    validation_date = models.DateTimeField(auto_now_add=True)

    display_name = models.CharField(max_length=255, blank=True, null=True, help_text=_(u'Le nom à afficher dans Truffe. Peut être utilisé pour préciser la fonction'))

    no_epfl_sync = models.BooleanField(default=False, help_text=_(u'A cocher pour ne pas synchroniser cette accréditation au niveau EPFL'))

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        unit_ro_access = True
        access = 'INFORMATIQUE'

    class MetaRights(UnitEditableModel.MetaRights):
        pass

    def __init__(self, *args, **kwargs):
        super(Accreditation, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'INGORE_PREZ': _(u'Peut supprimer le dernier président'),
        })

    def exp_date(self):
        """Returne la date d'expiration de l'accred"""
        return self.validation_date + datetime.timedelta(days=365)

    def is_valid(self):
        """Returne true si l'accred est valide"""
        return self.end_date is None

    def get_role_or_display_name(self):
        if self.display_name:
            return str(self.role) + " (" + self.display_name + ")"
        return str(self.role)

    def rights_can_INGORE_PREZ(self, user):
        return self.rights_in_root_unit(user, self.MetaRightsUnit.access)


class _AccessDelegation(GenericModel, UnitEditableModel):
    unit = FalseFK('units.models.Unit')

    access = MultiSelectField(choices=_Role.ACCESS_CHOICES, blank=True, null=True)
    valid_for_sub_units = models.BooleanField(_(u'Valide pour les sous-unités'), default=False, help_text=_(u'Si sélectionné, les accès supplémentaires dans l\'unité courante seront aussi valides dans les sous-unités'))

    user = models.ForeignKey(TruffeUser, blank=True, null=True, help_text=_(u'(Optionnel !) L\'utilisateur concerné. L\'utilisateur doit disposer d\'une accréditation dans l\'unité.'))
    role = FalseFK('units.models.Role', blank=True, null=True, help_text=_(u'(Optionnel !) Le rôle concerné.'))

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        unit_ro_access = True
        access = 'INFORMATIQUE'

    class MetaData:
        list_display = [
            ('id', ''),
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

        filter_fields = ()

        base_title = _(u'Délégation d\'accès')
        list_title = _(u'Liste de toutes les délégations d\'accès')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

        menu_id = 'menu-units-delegations'

        yes_or_no_fields = ['valid_for_sub_units']

        has_unit = True

        help_list = _(u"""Les délégations d'accès permettent de donner des accès supplémentaires dans une unité.

Les accès sont normalement déterminés en fonction des accréditations, au niveau global.
Par exemple, une personne accréditée en temps que 'Trésorier' dans une unité disposera de l'accès TRÉSOERIE pour l'unité.

Avec les délégations d'accês, il est par exemple possible de donner l'accès "COMMUNICATION" à tout les membres d'une unité en créant une délégations d'accès.

Il est aussi possible de restreindre une délégation â un utilisateur ou à un rôle particulier.""")

    class Meta:
        abstract = True

    def get_access(self):
        if self.access:
            return u', '.join(list(self.access))

    def __unicode__(self):
        return _(u'Accês supplémentaire n°%s' % (self.pk,))

    def delete_signal(self):
        self.save_signal()

    def save_signal(self):
        """Cleanup rights"""

        for user in self.unit.get_users():
            user.clear_rights_cache()
