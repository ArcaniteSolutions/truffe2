from notifications.models import Notification, NotificationRestriction, NotificationEmail
from django.contrib.contenttypes.models import ContentType


def notify_people(request, key, species, obj, users, metadata=None):

    for user in users:

        if request and user == request.user:
            continue

        n = Notification(key=key, species=species, linked_object=obj, user=user)
        n.save()

        if metadata:
            n.set_metadata(metadata)
            n.save()

        try:
            notification_restriction, __ = NotificationRestriction.objects.get_or_create(user=user, key=key)
        except NotificationRestriction.MultipleObjectsReturned:
            NotificationRestriction.objects.filter(user=user, key=key).delete()
            notification_restriction, __ = NotificationRestriction.objects.get_or_create(user=user, key=key)

        notification_restriction_all, __ = NotificationRestriction.objects.get_or_create(user=user, key='')

        if notification_restriction.autoread or notification_restriction_all.autoread:
            n.seen = True
            n.save()

        if not notification_restriction.no_email and not notification_restriction_all.no_email and Notification.objects.filter(key=key, species=species, object_id=obj.pk, content_type=ContentType.objects.get_for_model(obj), user=user, seen=False).count() == 1:
            NotificationEmail(user=user, notification=n, no_email_group=notification_restriction.no_email_group or notification_restriction_all.no_email_group).save()


def unotify_people(key, obj):

    Notification.objects.filter(key=key, object_id=obj.pk, content_type=ContentType.objects.get_for_model(obj), seen=False).update(seen=True)
