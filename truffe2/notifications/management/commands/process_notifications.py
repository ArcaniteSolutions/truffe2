from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _
from app.utils import send_templated_mail
from django.utils.timezone import now
from django.conf import settings


import datetime


from notifications.models import Notification, NotificationRestriction, NotificationEmail
from users.models import TruffeUser


class Command(BaseCommand):
    help = 'Send notifications'

    def handle(self, *args, **options):

        for user in NotificationEmail.objects.values('user').distinct():
            user = TruffeUser.objects.get(pk=user['user'])

            if not NotificationEmail.objects.filter(user=user, date__gt=(now()- datetime.timedelta(minutes=settings.NOTIFS_MINIMUM_BLANK))).exists() or NotificationEmail.objects.filter(user=user, date__lt=(now()- datetime.timedelta(minutes=settings.NOTIFS_MAXIMUM_WAIT))).exists():  # Si une notification plus veille que 15/NOTIFS_MAXIMUM_WAIT minutes OU pas de notification depuis 5/NOTIFS_MINIMUM_BLANK minutes

                notifications = list(NotificationEmail.objects.filter(user=user))

                if len(notifications) == 1:

                    context = {
                        'notification': notifications[0].notification,
                    }

                    send_templated_mail(None, _(u'Truffe :: Notification :: {}'.format(notifications[0].notification.key)), 'nobody@truffe.agepoly.ch', [user.email], 'notifications/mails/new_notif', context)

                else:

                    keys = []

                    for notif in notifications:
                        if notif.notification.key not in keys:
                            keys.append(notif.notification.key)

                    context = {
                        'notifications': map(lambda n: n.notification, notifications),
                    }

                    send_templated_mail(None, _(u'Truffe :: Notifications ({}) :: {}'.format(len(notifications), ', '.join(keys))), 'nobody@truffe.agepoly.ch', [user.email], 'notifications/mails/new_notifs', context)

                for notification in notifications:
                    notification.delete()
