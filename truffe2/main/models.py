# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, FalseFK, SearchableModel
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse


from rights.utils import AgepolyEditableModel, UnitEditableModel


import hashlib


class _HomePageNews(GenericModel, GenericStateModel, AgepolyEditableModel, SearchableModel):

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

        forced_pos = {
            '0_draft': (0.1, 0.5),
            '1_online': (0.5, 0.5),
            '2_archive': (0.9, 0.5),
        }

    class MetaSearch(SearchableModel.MetaSearch):

        fields = [
            'title',
            'content',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _Link(GenericModel, UnitEditableModel, SearchableModel):

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
        ('/gens/', _(u'Gens')),
        ('/communication/', _(u'Communication')),
        ('/logistics/', _(u'Logistique')),
        ('/logistics/vehicles', _(u'Logistique / Véhicules')),
        ('/logistics/rooms', _(u'Logistique / Salles')),
        ('/logistics/supply', _(u'Logistique / Matériel')),
        ('/units/', _(u'Unités et Accreds')),
        ('/accounting/', _(u'Finances')),
        ('/accounting/accounting', _(u'Finances / Compta')),
        ('/accounting/tools', _(u'Finances / Outils')),
        ('/accounting/proofs', _(u'Finances / Justifications')),
        ('/accounting/gestion', _(u'Finances / Gestion')),
        ('/cs/', _(u'Informatique')),
        ('/misc/', _(u'Divers')),
    )

    leftmenu = models.CharField(_(u'Position dans le menu de gauche'), max_length=128, choices=LEFTMENU_CHOICES, blank=True, null=True, help_text=_(u'Laisser blanc pour faire un lien normal. Réservé au comité de l\'AGEPoly. Attention, cache de 15 minutes !'))
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

        help_list = _(u"""Les liens sont affichés dans la banque de liens pour les différentes unités. Tu peux par exemple lister les différents services interne à ta commission.
"
Le comité de l'AGEPoly peut aussi afficher un lien dans le menu de gauche.""")

        extra_right_display = {
            'get_leftmenu_display': lambda (obj, user): obj.leftmenu,
            'icon': lambda (obj, user): obj.leftmenu,
        }

    class MetaEdit:

        only_if = {
            'leftmenu': lambda (instance, user): user.rights_in_root_unit(user, instance.MetaRightsUnit.access),
            'icon': lambda (instance, user): user.rights_in_root_unit(user, instance.MetaRightsUnit.access),
        }

    class MetaSearch(SearchableModel.MetaSearch):

        fields = [
            'title',
            'description',
            'url',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.url)

    def get_url(self):
        if self.url:
            return u'<a href="{}" target="_blank">{}</a>'.format(self.url, self.url)

    def __init__(self, *args, **kwargs):
        super(_Link, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'SHOW_BASE': _(u'Peut afficher la base de liens'),
        })

    def rights_can_SHOW_BASE(self, user):
        return self.rights_in_linked_unit(user)


class _SignableDocument(GenericModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsUniyt(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['PRESIDENCE']
        world_ro_access = False

    title = models.CharField(_(u'Titre'), max_length=255)
    description = models.TextField(_(u'Description'), blank=True, null=True)
    file = models.FileField(upload_to='uploads/signable_document/')

    active = models.BooleanField(_(u'Actif'), default=False)

    roles = models.ManyToManyField('units.Role')

    sha = models.CharField(max_length=255)

    class MetaData:
        list_display = [
            ('title', _(u'Titre')),
            ('get_roles_display', _(u'Rôles')),
        ]
        details_display = list_display + [
            ('description', _('Description')),
            ('get_file_link', _('Fichier')),
        ]
        filter_fields = ('title', 'description', 'roles__name')
        safe_fields = ['get_file_link']

        default_sort = "[1, 'asc']"  # title

        base_title = _(u'Documents à signer')
        list_title = _(u'Liste de tous les documents à signer')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-file-text-o'

        menu_id = 'menu-misc-documents'

        help_list = _(u"""Les différents documents à faire signer aux gens en fonction de leurs rôles.""")

    class MetaSearch(SearchableModel.MetaSearch):

        fields = [
            'title',
            'description',
        ]

    class Meta:
        abstract = True

    class MetaEdit:
        many_to_many_fields = ['roles']

        only_if = {
            'sha': lambda x: False,
        }

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.get_roles_display())

    def get_file_link(self):
        return u'<a href="{}">{}</a>'.format(reverse('main.views.signabledocument_download', args=(self.pk,)), self.file)

    def get_roles_display(self):
        return u', '.join([r.name for r in self.roles.order_by('name').all()])

    def should_sign(self, user):
        return user.accreditation_set.filter(role__in=self.roles.all(), end_date=None).exists()

    def signed(self, user):
        return self.signature_set.filter(user=user, document_sha=self.sha).first()

    def save(self, *args, **kwargs):
        super(_SignableDocument, self).save(*args, **kwargs)

        hash_sha = hashlib.sha256()

        with open(self.file.path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha.update(chunk)

        self.sha = hash_sha.hexdigest()

        super(_SignableDocument, self).save(*args, **kwargs)


class Signature(models.Model):

    user = models.ForeignKey('users.TruffeUser')
    document = models.ForeignKey('main.SignableDocument')
    when = models.DateTimeField(auto_now_add=True)
    ip = models.IPAddressField()
    useragent = models.CharField(max_length=255)
    document_sha = models.CharField(max_length=255)

    @property
    def is_valid(self):
        return self.document_sha == self.document.sha


class _File(GenericModel, AgepolyEditableModel, SearchableModel):

    class MetaRightsUniyt(AgepolyEditableModel.MetaRightsAgepoly):
        access = ['PRESIDENCE', 'TRESORERIE', 'INFORMATIQUE', 'COMMUNICATION']
        world_ro_access = False

    title = models.CharField(_(u'Titre'), max_length=255)
    description = models.TextField(_(u'Description'), blank=True, null=True)
    file = models.FileField(upload_to='uploads/files/')

    TYPE_ACCESS = [
        ('agep', _(u'Selement les membres d\'une unité')),
        ('all', _(u'Tous les utilisateurs')),
    ]

    access = models.CharField(_(u'Accès'), choices=TYPE_ACCESS, max_length=64, default='agep')

    TYPE_GROUP = [
        ('accounting', _(u'Finances')),
        ('cs', _(u'Informatique')),
        ('misc', _(u'Divers')),
    ]

    group = models.CharField(_(u'Groupe'), choices=TYPE_GROUP, max_length=64, default='misc')

    class MetaData:
        list_display = [
            ('title', _(u'Titre')),
            ('get_group_display', _(u'Groupe')),
            ('get_access_display', _(u'Accès')),
        ]
        details_display = list_display + [
            ('description', _('Description')),
            ('get_file_link', _('Fichier')),
        ]
        filter_fields = ('title', 'group', 'access', 'description')
        safe_fields = ['get_file_link']

        default_sort = "[1, 'asc']"  # title

        base_title = _('Fichiers')
        list_title = _(u'Liste de tous les fichiers')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-file-text-o'

        menu_id = 'menu-misc-files'

        help_list = _(u"""Les différents fichiers publics disponibles dans truffe 2.

Les fichiers sont regroupés en différents groupes accessibles depuis le menu latéral.""")

    class MetaSearch(SearchableModel.MetaSearch):

        fields = [
            'title',
            'description',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.get_group_display())

    def __init__(self, *args, **kwargs):
        super(_File, self).__init__(*args, **kwargs)

        self.MetaRights = type("MetaRights", (self.MetaRights,), {})
        self.MetaRights.rights_update({
            'DOWNLOAD': _(u'Peut télécharger le fichier'),
            'LIST_ACCOUNTING': _(u'Peut affichier la liste des fichiers pour les finances'),
            'LIST_CS': _(u'Peut affichier la liste des fichiers pour l\'informatique'),
            'LIST_MISC': _(u'Peut affichier la liste des fichiers divers'),
        })

    def rights_can_DOWNLOAD(self, user):
        if user.is_external():
            return self.access == 'all'
        return True  # Everyone else can download

    def check_if_can(self, user, group):

        l = self.__class__.objects.filter(group=group, deleted=False)

        if user.is_external():
            l = l.filter(access='all')

        return l.exists()

    def get_file_link(self):
        return u'<a href="{}">{}</a>'.format(reverse('main.views.file_download', args=(self.pk,)), self.file)

    def rights_can_LIST_ACCOUNTING(self, user):
        return self.check_if_can(user, 'accounting')

    def rights_can_LIST_CS(self, user):
        return self.check_if_can(user, 'cs')

    def rights_can_LIST_MISC(self, user):
        return self.check_if_can(user, 'misc')
