# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel
from django.utils.translation import ugettext_lazy as _

from rights.utils import AgepolyEditableModel


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
        status_col_id = 3

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title
