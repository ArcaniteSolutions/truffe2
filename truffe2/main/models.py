# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, FalseFK
from django.utils.translation import ugettext_lazy as _

from rights.utils import AgepolyEditableModel, UnitEditableModel


class _HomePageNews(GenericModel, GenericStateModel, AgepolyEditableModel):

    class MetaRightsAgepoly(AgepolyEditableModel.MetaRightsAgepoly):
        access = 'COMMUNICATION'
        world_ro_access = False

    title = models.CharField(max_length=255)
    content = models.TextField()

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def may_switch_to(self, user, dest_state):
        if self.rights_can('EDIT', user):
            return super(_HomePageNews, self).may_switch_to(user, dest_state)
        return False

    def can_switch_to(self, user, dest_state):

        if self.status == '2_archive' and not user.is_superuser:
            return (False, _(u'Seul un super utilisateur peut sortir cet élément de l\'état archivé'))

        if not self.rights_can('EDIT', user):
            return (False, _('Pas les droits'))

        return super(_HomePageNews, self).can_switch_to(user, dest_state)

    def rights_can_EDIT(self, user):
        if self.status == '2_archive':
            return False
        return super(_HomePageNews, self).rights_can_EDIT(user)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]
        details_display = list_display + [('content', _('Content'))]
        filter_fields = ('title', 'status')

        default_sort = "[1, 'asc']"  # title

        base_title = _('News Truffe')
        list_title = _(u'Liste de toutes les news Truffe')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-bullhorn'

        menu_id = 'menu-communication-homepagenews'

        datetime_fields = ['start_date', 'end_date']

        help_list = _(u"""Les news Truffe sont les nouvelles affichées sur la page d'accueil de Truffe.""")

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

    class MetaState:
        states = {
            '0_draft': _('Brouillon'),
            '1_online': _('En ligne'),
            '2_archive': _(u'Archivé'),
        }
        default = '0_draft'

        states_links = {
            '0_draft': ['1_online', '2_archive'],
            '1_online': ['0_draft', '2_archive'],
            '2_archive': [],
        }

        states_colors = {
            '0_draft': 'primary',
            '1_online': 'success',
            '2_archive': 'default',
        }

        states_icons = {
            '0_draft': '',
            '1_online': '',
            '2_archive': '',
        }

        states_texts = {
            '0_draft': _(u'La news est en cours de création et n\'est pas affichée sur la page d\'accueil.'),
            '1_online': _(u'La news est finalisée et sera affichée sur la page d\'accueil aux dates prévues.'),
            '2_archive': _(u'La news est archivée et n\'est plus affichée sur la page d\'accueil. Elle n\'est plus modifiable.'),
        }

        states_default_filter = '0_draft,1_online'
        status_col_id = 4

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _Link(GenericModel, UnitEditableModel):

    class MetaRightsUniyt(UnitEditableModel.MetaRightsUnit):
        access = ['PRESIDENCE', 'INFORMATIQUE', 'COMMUNICATION']
        world_ro_access = False

    title = models.CharField(_(u'Titre'), max_length=255)
    description = models.TextField(_(u'Description'), blank=True, null=True)
    url = models.URLField()

    unit = FalseFK('units.models.Unit')

    LEFTMENU_CHOICES = (
        ('/main/top', _(u'Principal / En haut')),
        ('/main/bottom', _(u'Principal / En bas')),
        ('/admin/', _(u'Admin')),
        ('/communication/', _(u'Communication')),
        ('/logitics/', _(u'Logistique')),
        ('/logitics/vehicles', _(u'Logistique / Véhicules')),
        ('/logitics/rooms', _(u'Logistique / Salles')),
        ('/logitics/supply', _(u'Logistique / Matériel')),
        ('/units/', _(u'Unités et Accreds')),
        ('/accounting/', _(u'Compta')),
        ('/accounting/accounting', _(u'Compta / Compta')),
        ('/accounting/gestion', _(u'Compta / Gestion')),
        ('/accounting/tools', _(u'Compta / Outils')),
        ('/accounting/prrofs', _(u'Compta / Justifications')),
    )

    leftmenu = models.CharField(_(u'Position dans le menu de gauche'), max_length=128, choices=LEFTMENU_CHOICES, blank=True, null=True, help_text=_(u'Laisser blanc pour faire un lien normal. Réservé au comité de l\'AGEPoly'))
    icon = models.CharField(_(u'Icone FontAwesome'), max_length=128, default='fa-external-link-square')

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('get_url', _(u'URL')),
        ]
        details_display = list_display + [
            ('description', _('Description')),
            ('get_leftmenu_display', _('Menu de gauche')),
            ('icon', _('Icone')),
        ]
        filter_fields = ('title', 'url', 'description')
        safe_fields = ['get_url']

        default_sort = "[1, 'asc']"  # title

        base_title = _('Liens')
        list_title = _(u'Liste de toutes les liens')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-link'

        menu_id = 'menu-misc-links'

        has_unit = True

        help_list = _(u"""Les liens sont affiché dans la banque de liens pour les différentes unités. Tu peux par exemple lister les différents services interne à ta commision.

Le comité de l'AGEPoly peut aussi afficher un lien dans le menu de gauche.""")

        extra_right_display = {
            'leftmenu': lambda (obj, user): obj.leftmenu,
            'icon': lambda (obj, user): obj.leftmenu,
        }

    class MetaEdit:

        only_if = {
            'get_leftmenu_display': lambda (instance, user): user.rights_in_root_unit(user, instance.MetaRightsUnit.access),
            'icon': lambda (instance, user): user.rights_in_root_unit(user, instance.MetaRightsUnit.access),
        }

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.url)

    def get_url(self):
        if self.url:
            return u'<a href="{}" target="_blank">{}</a>'.format(self.url, self.url)
