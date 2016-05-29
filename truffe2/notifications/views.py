# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.timezone import now


from notifications.models import Notification, NotificationRestriction
from generic.datatables import generic_list_json


@login_required
def dropdown(request):
    """Display the downdown menu for notificatoins"""

    if request.GET.get('read'):
        notification = get_object_or_404(Notification, pk=request.GET.get('read'), user=request.user)
        notification.seen = True
        notification.seen_date = now()
        notification.save()

    if request.GET.get('allread'):
        Notification.objects.filter(user=request.user, seen=False).update(seen=True, seen_date=now())
        pass

    notifications = Notification.objects.filter(user=request.user, seen=False).order_by('-creation_date')

    return render(request, 'notifications/dropdown.html', {'notifications': notifications})


@login_required
def goto(request, pk):

    notification = get_object_or_404(Notification, pk=pk, user=request.user)

    notification.seen = True
    notification.seen_date = now()
    notification.save()

    return HttpResponseRedirect(request.GET.get('next'))


@login_required
def notifications_count(request):

    if request.user.pk:
        notifications = Notification.objects.filter(user=request.user, seen=False)
        return {'notifications_count': notifications.count()}
    else:
        return {'notifications_count': 0}


@login_required
def notification_center(request):
    """Base display for the notification center"""

    return render(request, 'notifications/center/index.html', {})


@login_required
def notification_keys(request):
    """Display left type menu"""

    keys = []

    for key in Notification.objects.filter(user=request.user).values('key').distinct():
        key['nb_unread'] = Notification.objects.filter(user=request.user, seen=False, key=key['key']).count()
        keys.append(key)

    keys = sorted(keys, key=lambda x: x['key'])

    regrouped_keys = {}

    for key in keys:

        cindex = regrouped_keys
        subkeys = key['key'].split('.')

        pathkey = ''

        for skey in subkeys:

            if not pathkey:
                pathkey = skey
            else:
                pathkey = u'{}.{}'.format(pathkey, skey)

            if 'subkeys' not in cindex:
                cindex['subkeys'] = {}

            if 'unread_count' not in cindex:
                cindex['unread_count'] = 0

            if skey not in cindex['subkeys']:
                cindex['subkeys'][skey] = {}

            cindex['unread_count'] += key['nb_unread']
            cindex = cindex['subkeys'][skey]
            cindex['pathkey'] = pathkey

            if 'unread_count' not in cindex:
                cindex['unread_count'] = 0

        if 'level_keys' not in cindex:
            cindex['level_keys'] = []

        key['last_key'] = subkeys[-1]
        cindex['level_keys'].append(key)
        cindex['unread_count'] += key['nb_unread']

    def cleanup_keys(cindex, papa=None):

        modif = False

        for ___, subkey in cindex.get('subkeys', {}).items():
            modif = modif or cleanup_keys(subkey, cindex)

        if papa:

            for kindex, subkey in cindex.get('subkeys', {}).items():

                if subkey.get('subkeys'):  # Clean only if subkey has no subkeys
                    continue

                if subkey.get('level_keys') and len(subkey['level_keys']) == 1:  # If the subkey has only one key

                    if 'level_keys' not in cindex:
                        cindex['level_keys'] = []

                    alone_key = subkey['level_keys'][0]

                    if not alone_key.get('already_movedup'):
                        alone_key['already_movedup'] = True
                    else:
                        alone_key['last_key'] = u'{}.{}'.format(kindex, alone_key.get('last_key'))

                    # Move the key up
                    cindex['level_keys'].append(alone_key)

                    # Remove the subkey
                    del cindex['subkeys'][kindex]

                    modif = True

        return modif

    while cleanup_keys(regrouped_keys):
        pass

    all_unread = Notification.objects.filter(user=request.user, seen=False).count()

    return render(request, 'notifications/center/keys.html', {'keys': regrouped_keys, 'current_type': request.GET.get('current_type'), 'all_unread': all_unread})


@login_required
@csrf_exempt
def notification_json(request):
    """Json for notifications"""

    current_type = request.GET.get('current_type')

    if current_type:
        bonus_filter = lambda x: x.filter(key__startswith=current_type, user=request.user)
    else:
        bonus_filter = lambda x: x.filter(user=request.user)

    return generic_list_json(request, Notification, ['creation_date', 'key', 'linked_object', 'pk', 'pk'], 'notifications/center/json.html', bonus_filter_function=bonus_filter)


@login_required
def notification_restrictions(request):

    key = request.GET.get('current_type')

    if Notification.objects.filter(user=request.user, key=key).exists():
        notification_restriction, __ = NotificationRestriction.objects.get_or_create(user=request.user, key=key)
    else:
        notification_restriction = None

    return render(request, 'notifications/center/restrictions.html', {'key': key, 'notification_restriction': notification_restriction})


@login_required
def notification_restrictions_update(request):

    key = request.GET.get('current_type')

    notification_restriction, __ = NotificationRestriction.objects.get_or_create(user=request.user, key=key)
    notification_restriction.no_email = request.GET.get('mail') == 'true'
    notification_restriction.autoread = request.GET.get('mute') == 'true'
    notification_restriction.no_email_group = request.GET.get('no_group') == 'true'

    if notification_restriction.autoread and not notification_restriction.no_email:

        if 'mail' in request.GET.get('elem'):
            notification_restriction.autoread = False
        else:
            notification_restriction.no_email = True

    notification_restriction.save()

    return HttpResponse()


@login_required
def mark_as_read(request):
    """Display the downdown menu for notificatoins"""

    notification = get_object_or_404(Notification, pk=request.GET.get('pk'), user=request.user)
    notification.seen = True
    notification.seen_date = now()
    notification.save()

    return HttpResponse('')
