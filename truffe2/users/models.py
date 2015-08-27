# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager
from django.core.cache import cache
from django.core.urlresolvers import reverse

from rights.utils import ModelWithRight
from generic.search import SearchableModel

import re
import time


class TruffeUserManager(BaseUserManager):

    def _create_user(self, username, password, is_superuser, **extra_fields):
        """Creates and saves a User with the given username and password."""
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        user = self.model(username=username, is_active=True, is_superuser=is_superuser, last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        return self._create_user(username, password, True, **extra_fields)


class TruffeUser(AbstractBaseUser, PermissionsMixin, ModelWithRight, SearchableModel):
    username = models.CharField(_('Sciper ou username'), max_length=255, unique=True)
    first_name = models.CharField(_(u'Prénom'), max_length=100, blank=True)
    last_name = models.CharField(_('Nom de famille'), max_length=100, blank=True)
    email = models.EmailField(_('Adresse email'), max_length=255)
    email_perso = models.EmailField(_(u'Adresse email privée'), max_length=255, blank=True, null=True)
    is_active = models.BooleanField(_('Actif'), default=True, help_text=_(u'Défini si cet utilisateur doit être considéré comme actif. Désactiver ceci au lieu de supprimer le compte.'))
    is_betatester = models.BooleanField(_('Betatesteur'), default=False, help_text=_(u'Rend visible les éléments en cours de développement'))
    date_joined = models.DateTimeField(_('Date d\'inscription'), default=timezone.now)

    mobile = models.CharField(max_length=25, blank=True)
    adresse = models.TextField(blank=True)
    nom_banque = models.CharField(max_length=128, blank=True, help_text=_('Pour la poste, mets Postfinance. Sinon, mets le nom de ta banque.'))
    iban_ou_ccp = models.CharField(max_length=128, blank=True, help_text=_('Pour la poste, mets ton CCP. Sinon, mets ton IBAN'))

    body = models.CharField(max_length=1, default='.')  # Saved body classes (to save layout options of the user)
    homepage = models.TextField(blank=True, null=True)  # Saved homepage order (to save layout options of the user)

    avatar = models.ImageField(upload_to='uploads/avatars/', help_text=_(u'Si pas renseigné, utilise la photo EPFL. Si pas de photo EPFL publique, utilise un poney.'), blank=True, null=True)

    objects = TruffeUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    class MetaRights(ModelWithRight.MetaRights):
        pass

    def __init__(self, *args, **kwargs):
        super(TruffeUser, self).__init__(*args, **kwargs)

        self.MetaRights.rights_update({
            'CREATE': _(u'Peut créer un nouvel utilisateur'),
            'EDIT': _(u'Peut editer un utilisateur'),
            'SHOW': _(u'Peut afficher un utilisateur'),
            'FULL_SEARCH': _(u'Peut utiliser la recherche sans filtrage préliminaire'),
        })

    def rights_can_SHOW(self, user):
        return True

    def rights_can_CREATE(self, user):
        return self.rights_in_root_unit(user, access='INFORMATIQUE')

    def rights_can_EDIT(self, user):
        return self == user or self.rights_in_root_unit(user, access='INFORMATIQUE')

    def rights_can_FULL_SEARCH(self, user):
        return self.rights_in_root_unit(user, access=['PRESIDENCE', 'SECRETARIAT'])

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def generate_vcard(self, source_user):
        """Generate the user's vcard"""

        retour = u"""BEGIN:VCARD
N:%s;%s
EMAIL;INTERNET:%s
""" % (self.first_name, self.last_name, self.email)
        if UserPrivacy.user_can_access(source_user, self, 'mobile'):
            retour += u"""TEL;CELL:%s
""" % (self.mobile, )
        retour += u"""END:VCARD"""

        return retour

    def get_roles(self):
        return ', '.join(['%s: %s' % (x.unit, x.role,) for x in list(self.active_accreds())])

    def active_accreds(self, with_hiddens=False):
        liste = self.accreditation_set.filter(end_date=None)

        if not with_hiddens:
            liste = liste.filter(hidden_in_truffe=False)

        return liste.order_by('unit__name', 'role__ordre')

    def rights_in_any_unit(self, access):
        for accred in self.active_accreds(with_hiddens=True):
            # Ask the coresponding unit to do the check.
            if accred.unit.is_user_in_groupe(self, access, no_parent=True):
                return True

        return False

    def is_external(self):
        return not self.active_accreds(with_hiddens=True)

    def username_is_sciper(self):
        return re.match('^\d{6}$', self.username)

    def old_accreds(self):
        return self.accreditation_set.exclude(end_date=None).order_by('unit__name', 'role__ordre', 'start_date', 'end_date')

    def clear_rights_cache(self):
        cache.set('right~user_%s' % (self.pk,), time.time())

    def __unicode__(self):
        return '%s (%s)' % (self.get_full_name(), self.username)

    def is_profile_ok(self):
        return self.iban_ou_ccp and self.mobile and self.nom_banque and self.adresse and self.first_name and self.last_name

    def display_url(self):
        return reverse('users.views.users_profile', args=(self.pk,))

    class MetaData:
        base_title = _(u'Utilisateur')
        elem_icon = 'fa fa-user'

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u'user personne gens'

        last_edit_date_field = 'date_joined'

        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
        ]


class UserPrivacy(models.Model):
    user = models.ForeignKey(TruffeUser)

    FIELD_CHOICES = (
        ('mobile', _('Mobile')),
        ('adresse', _('Adresse')),
        ('nom_banque', _('Nom banque')),
        ('iban_ou_ccp', _('IBAN ou CCP')),
        ('email_perso', _(u'Adresse email privée'))
    )

    field = models.CharField(max_length=64, choices=FIELD_CHOICES)

    LEVEL_CHOICES = (
        ('prive', _(u'Privé')),
        ('groupe', _(u'Membres de mes groupes')),
        ('member', _(u'Accrédités AGEPoly')),
        ('public', _(u'Public'))
    )

    level = models.CharField(max_length=64, choices=LEVEL_CHOICES)

    @staticmethod
    def get_privacy_for_field(user, field):
        try:
            return UserPrivacy.objects.get(user=user, field=field).level
        except UserPrivacy.DoesNotExist:
            UserPrivacy(user=user, field=field, level='prive').save()
            return 'prive'

    @staticmethod
    def user_can_access(user_reader, user_readed, field):
        level = UserPrivacy.get_privacy_for_field(user_readed, field)

        if user_reader == user_readed or user_reader.is_superuser or user_readed.rights_can('EDIT', user_reader):
            return True
        else:
            if level == 'public':
                return True
            if level == 'prive':
                return False
            if level == 'member':
                return user_reader.accreditation_set.filter(end_date=None).count() > 0
            if level == 'groupe':
                my_groups = [a.unit.pk for a in list(user_readed.accreditation_set.filter(end_date=None))]
                return user_reader.accreditation_set.filter(end_date=None, unit__pk__in=my_groups).count() > 0
