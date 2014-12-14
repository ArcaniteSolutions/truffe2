from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.conf import settings

from django.utils.translation import ugettext_lazy as _


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

    def get_template(self):
        return 'notifications/species/%s.html' % (self.species,)

    def get_email_template(self):
        return 'notifications/species/mails/%s.html' % (self.species,)
