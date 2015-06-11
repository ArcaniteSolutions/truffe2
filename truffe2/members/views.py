# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext

from app.utils import update_current_unit, get_current_unit
from generic.datatables import generic_list_json

import json


@login_required
def membership_edit(request, pk):
    pass


@login_required
def load_list(request, pk):
    """Charge la liste des membres dans le groupe donné en argument"""
    from members.models import MemberSet

    memberset = MemberSet.objects.get(pk=pk)

    if not memberset.rights_can('SHOW', request.user):
        raise Http404

    header = [ugettext('Utilisateur'), ugettext('Date d\'ajout')]
    memberships = memberset.membership_set.all()
    body = map(lambda membership: [membership.pk, membership.user.get_full_name(),
                                   str(membership.adding_date)], memberships)

    if memberset.handle_fees:
        header += [ugettext(u'Cotisation payée')]
        body = map(lambda membership: [membership.pk, membership.user.get_full_name(),
                                       str(membership.adding_date), membership.payed_fees], memberships)

    return HttpResponse(json.dumps({'header': header, 'body': body}))


@login_required
@csrf_exempt
def membership_list_json(request, pk):
    """Display the list of members, json call for the list"""
    from members.models import MemberSet, Membership

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    unit = get_current_unit(request)

    # Get the MemberSet
    memberset = MemberSet.objects.get(pk=pk)

    # Check unit access
    if not memberset.rights_can('SHOW', request.user):
        raise Http404

    # Filter by unit
    filter2 = lambda x: x.filter(group=memberset)

    return generic_list_json(request, Membership, ['user', 'adding_date', 'payed_due_fees', 'group', 'pk'], 'members/membership/list_json.html', bonus_data={'handle_fees': memberset.handle_fees}, filter_fields=['user__first_name', 'user__last_name', 'user__username'], bonus_filter_function=filter2)


@login_required
def export_members(request, pk):
    from members.models import MemberSet

    memberset = MemberSet.objects.get(pk=pk)

    if not memberset.rights_can('EDIT', request.user):
        raise Http404

    list_users = map(lambda membership: membership.user, memberset.membership_set.all())
    export_list = []
    for user in list_users:
        if user.username_is_sciper():
            export_list.append(user.username)
        else:
            export_list.append([user.first_name, user.last_name, user.email])

    return json.dumps(export_list)


@login_required
def import_members(request, pk):
    pass
