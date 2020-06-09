from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _
from app.utils import send_templated_mail
from django.utils.timezone import now
from django.conf import settings


import datetime


from notifications.models import NotificationEmail
from users.models import TruffeUser


class Command(BaseCommand):
    help = 'Send notifications'

    def handle(self, *args, **options):

        for user in NotificationEmail.objects.values('user').distinct():
            user = TruffeUser.objects.get(pk=user['user'])

            if settings.DEBUG or not NotificationEmail.objects.filter(user=user, date__gt=(now() - datetime.timedelta(minutes=settings.NOTIFS_MINIMUM_BLANK))).exists() or NotificationEmail.objects.filter(user=user, date__lt=(now() - datetime.timedelta(minutes=settings.NOTIFS_MAXIMUM_WAIT))).exists():  # Si une notification plus veille que 15/NOTIFS_MAXIMUM_WAIT minutes OU pas de notification depuis 5/NOTIFS_MINIMUM_BLANK minutes

                notifications = list(NotificationEmail.objects.filter(user=user))

                groups_notifications = []
                alone_notifications = []

                for notification in notifications:
                    if notification.no_email_group:
                        alone_notifications.append(notification)
                    else:
                        groups_notifications.append(notification)

                if len(groups_notifications) == 1:
                    alone_notifications.append(groups_notifications.pop())

                for notification in alone_notifications:

                    context = {
                        'notification': notification.notification,
                    }
                    send_templated_mail(None, _(u'Truffe :: Notification :: {}'.format(notification.notification.key)), 'nobody@truffe.agepoly.ch', [user.email], 'notifications/mails/new_notif', context)

                if groups_notifications:

                    keys = []

                    for notif in groups_notifications:
                        if notif.notification.key not in keys:
                            keys.append(notif.notification.key)

                    context = {
                        'notifications': map(lambda n: n.notification, groups_notifications),
                    }
                    send_templated_mail(None, _(u'Truffe :: Notifications ({}) :: {}'.format(len(groups_notifications), ', '.join(keys))), 'nobody@truffe.agepoly.ch', [user.email], 'notifications/mails/new_notifs', context)

                for notification in notifications:
                    notification.delete()
