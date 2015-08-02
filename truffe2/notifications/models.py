from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


import json


class Notification(models.Model):
    key = models.CharField(max_length=255)

    species = models.CharField(max_length=255)

    creation_date = models.DateTimeField(auto_now_add=True)
    seen_date = models.DateTimeField(blank=True, null=True)

    seen = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    linked_object = generic.GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    metadata = models.TextField(blank=True, null=True)

    def set_metadata(self, data):
        self.metadata = json.dumps(data)

    def get_metadata(self):
        return json.loads(self.metadata)

    def get_template(self):
        return 'notifications/species/%s.html' % (self.species,)

    def get_email_template(self):
        return 'notifications/species/mails/%s.html' % (self.species,)

    def get_center_message_template(self):
        return 'notifications/species/center/message/%s.html' % (self.species,)

    def get_center_buttons_template(self):
        return 'notifications/species/center/buttons/%s.html' % (self.species,)


class NotificationRestriction(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    key = models.CharField(max_length=255)

    no_email = models.BooleanField(default=False)
    autoread = models.BooleanField(default=False)


class NotificationEmail(models.Model):

    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    notification = models.ForeignKey(Notification)
