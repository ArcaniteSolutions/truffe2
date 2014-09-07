# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel
from django.utils.translation import ugettext_lazy as _

from users.models import TruffeUser

import datetime
from multiselectfield import MultiSelectField

from rights.utils import AgepolyEditableModel, UnitEditableModel

from django.conf import settings


class _Unit(GenericModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'INFORMATIQUE'
        world_ro_access = True

    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=64, blank=True, null=True, help_text=_(u'Utilisé pour la syncronisation des accréditations'))
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    is_commission = models.BooleanField(default=False, help_text=_(u'Cocher si cette unité est une commission de l\'AGEPoly'))
    is_equipe = models.BooleanField(default=False, help_text=_(u'Cocher si cette unité est une équipe de l\'AGEPoly'))

    parent_herachique = models.ForeignKey('Unit', blank=True, null=True, help_text=_(u'Pour les commission, sélectionner le comité de l\'AGEPoly. Pour les sous-commisions, sélectionner la commission parente. Pour un sous-coaching, sélectionner la commission coaching. Pour le comité de l\'AGEPoly, ne rien mettre.'))

    class MetaData:
        list_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_herachique', _('Parent')),
            ('president', _('President'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_herachique', _('Parent')),
            ('president', _('President'))
        ]

        yes_or_no_fields = ['is_commission', 'is_equipe']

        filter_fields = ('name', )

        base_title = _(u'Unités')
        list_title = _(u'Liste de toutes les unités')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

        menu_id = 'menu-units-units'

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

    def is_user_in_groupe(self, user, access=None):

        for accreditation in self.accreditation_set.filter(user=user, end_date=None):
            if accreditation.is_valid():
                if not access or access in accreditation.role.access:
                    return True

        if self.parent_herachique:
            return self.parent_herachique.is_user_in_groupe(user, access)
        return False

    @property
    def president(self):
        return ', '.join([u.user.get_full_name() for u in list(self.accreditation_set.filter(end_date=None, role__pk=settings.PRESIDENT_ROLE_PK))])

    def can_delete(self):

        if self.accreditation_set.count():
            return (False, _(u'Au moins une accéditation existe avec cette unité, impossible de supprimer l\'unité (NB: Historique compris).'))

        return (True, None)

    def current_accreds(self):
        return self.accreditation_set.filter(end_date=None).order_by('role__ordre', 'user__first_name', 'user__last_name')


class _Role(GenericModel, AgepolyEditableModel):
    """Un role, pour une accred"""

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'INFORMATIQUE'
        world_ro_access = True

    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=255, null=True, blank=True, help_text=_(u'Mettre ici l\'ID accred du role pour la syncronisation EPFL'))
    description = models.TextField(null=True, blank=True)
    ordre = models.IntegerField(null=True, blank=True, help_text=_(u'Il n\'est pas possible d\'acréditer la même personne dans la même unité plusieurs fois. Le role avec le plus PETIT ordre sera prit en compte'))

    ACCESS_CHOICES = (
        ('PRESIDENCE', ('Présidence')),
        ('TRESORERIE', ('Trésorerie')),
        ('COMMUNICATION', ('Communication')),
        ('INFORMATIQUE', ('Informatique')),
        ('LOGISTIQUE', ('Logistique')),
        ('SECRETARIAT', ('Secrétariat'))
    )

    access = MultiSelectField(choices=ACCESS_CHOICES, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def get_access(self):
        return ', '.join(self.access)

    class MetaData:
        list_display = [
            ('name', _('Nom')),
            ('id_epfl', _('ID EPFL ?')),
            ('ordre', _(u'Ordre'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('description', _('Description')),
            ('id_epfl', _('ID EPFL ?')),
            ('ordre', _(u'Ordre')),
            ('get_access', _(u'Accès')),
        ]

        filter_fields = ('name', 'id_epfl', 'description')

        base_title = _(u'Roles')
        list_title = _(u'Liste de toutes les roles')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

        menu_id = 'menu-units-roles'

    class Meta:
        abstract = True

    def can_delete(self):

        if self.accreditation_set.count():
            return (False, _(u'Au moins une accéditation existe avec ce role, impossible de supprimer le role (NB: Historique compris)'))

        return (True, None)


class Accreditation(models.Model, UnitEditableModel):
    unit = models.ForeignKey('Unit')
    user = models.ForeignKey(TruffeUser)
    role = models.ForeignKey('Role')

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    validation_date = models.DateTimeField(auto_now_add=True)

    display_name = models.CharField(max_length=255, blank=True, null=True, help_text=_(u'Le nom a afficher dans truffe. Peut être utilisé pour préciser la fonction'))

    no_epfl_sync = models.BooleanField(default=False, help_text=_(u'Checker cette coche pour ne pas sycroniser cette accrédiation au niveau EPFL'))

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
