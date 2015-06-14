from notifications.models import Notification, NotificationRestriction
from django.contrib.contenttypes.models import ContentType

from django.utils.translation import ugettext_lazy as _
from app.utils import send_templated_mail


def notify_people(request, key, species, obj, users, metadata=None):

    for user in users:

        if request and user == request.user:
            continue

        n = Notification(key=key, species=species, linked_object=obj, user=user)
        n.save()

        if metadata:
            n.set_metadata(metadata)
            n.save()

        notification_restriction, __ = NotificationRestriction.objects.get_or_create(user=user, key=key)
        notification_restriction_all, __ = NotificationRestriction.objects.get_or_create(user=user, key='')

        if notification_restriction.autoread or notification_restriction_all.autoread:
            n.seen = True
            n.save()

        if not notification_restriction.no_email and not notification_restriction_all.no_email and Notification.objects.filter(key=key, species=species, object_id=obj.pk, content_type=ContentType.objects.get_for_model(obj), user=user, seen=False).count() == 1:

            context = {
                'notification': n,
            }

            send_templated_mail(request, _('Truffe :: Notification :: %s') % (key,), 'nobody@truffe.agepoly.ch', [user.email], 'notifications/mails/new_notif', context)


def unotify_people(key, obj):

    Notification.objects.filter(key=key, object_id=obj.pk, content_type=ContentType.objects.get_for_model(obj), seen=False).update(seen=True)
