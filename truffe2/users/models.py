# -*- coding: utf-8 -*-
from django.db import models

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.contrib.auth.models import BaseUserManager


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


class TruffeUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('Sciper or username'), max_length=255, unique=True)
    email = models.EmailField(_('Email address'), max_length=255, blank=True)
    first_name = models.CharField(_('First name'), max_length=100, blank=True)
    last_name = models.CharField(_('Last name'), max_length=100, blank=True)
    is_active = models.BooleanField(_('Active'), default=True, help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)

    mobile = models.CharField(max_length=25, blank=True)
    adresse = models.TextField(blank=True)
    nom_banque = models.CharField(max_length=128, blank=True, help_text=_('Pour la poste, met Postfinance. Sinon, met le nom de ta banque.'))
    iban_ou_ccp = models.CharField(max_length=128, blank=True, help_text=_('Pour la poste, met ton CCP. Sinon, met ton IBAN'))

    body = models.CharField(max_length=1, default='.')

    objects = TruffeUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

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


class UserPrivacy(models.Model):
    user = models.ForeignKey(TruffeUser)

    FIELD_CHOICES = (
        ('mobile', _('Mobile')),
        ('adresse', _('Adresse')),
        ('nom_banque', _('Nom banque')),
        ('iban_ou_ccp', _('Iban ou ccp'))
    )

    field = models.CharField(max_length=64, choices=FIELD_CHOICES)

    LEVEL_CHOICES = (
        ('prive', _(u'Privé')),
        ('groupe', _(u'Membre de mes groupes')),
        ('member', _(u'Acredité AGEPoly')),
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

        if user_reader == user_readed or user_reader.is_superadmin:
            return True
        else:
            return level == 'public'  # Todo: Implement corectly