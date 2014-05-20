# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel
from django.utils.translation import ugettext_lazy as _

from users.models import TruffeUser

import datetime

class _Unit(GenericModel):

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
            ('parent_herachique', _('Parent'))
        ]

        details_display = [
            ('name', _('Nom')),
            ('is_commission', _('Commission ?')),
            ('is_equipe', _(u'Équipe ?')),
            ('parent_herachique', _('Parent'))
        ]

        filter_fields = ('name', )

        base_title = _(u'Unités')
        list_title = _(u'Liste de toutes les unités')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

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
        return self.unit_set.filter(is_commission=True).filter(deleted=False).order_by('name')

    def sub_eqi(self):
        """Return the sub units, but only groups"""
        return self.unit_set.exclude(is_commission=True).filter(is_equipe=True).filter(deleted=False).order_by('name')

    def sub_grp(self):
        """Return the sub units, without groups or commissions"""
        return self.unit_set.filter(is_commission=False).filter(is_equipe=False).filter(deleted=False).order_by('name')


class _Role(GenericModel):
    """Un role, pour une accred"""
    name = models.CharField(max_length=255)
    id_epfl = models.CharField(max_length=255, null=True, blank=True, help_text=_(u'Mettre ici l\'ID accred du role pour la syncronisation EPFL'))
    description = models.TextField(null=True, blank=True)
    ordre = models.IntegerField(null=True, blank=True, help_text=_(u'Il n\'est pas possible d\'acréditer la même personne dans la même unité plusieurs fois. Le role avec le plus PETIT ordre sera prit en compte'))

    def __unicode__(self):
        return self.name

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
        ]

        filter_fields = ('name', 'id_epfl', 'description')

        base_title = _(u'Roles')
        list_title = _(u'Liste de toutes les roles')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-group'

    class Meta:
        abstract = True


class Accreditation(models.Model):
    unite = models.ForeignKey('Unit')
    user = models.ForeignKey(TruffeUser)
    role = models.ForeignKey('Role')

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    validation_date = models.DateTimeField(auto_now_add=True)

    display_name = models.CharField(max_length=255, blank=True, null=True, help_text=_(u'Le nom a afficher dans truffe. Peut être utilisé pour préciser la fonction'))

    no_epfl_sync = models.BooleanField(default=False, help_text=_(u'Checker cette coche pour ne pas sycroniser cette accrédiation au niveau EPFL'))

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
