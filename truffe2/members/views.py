# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import now
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from app.ldaputils import get_attrs_of_sciper
from app.utils import update_current_unit, get_current_unit
from members.forms2 import MembershipAddForm
from generic.views import generate_edit
from generic.datatables import generic_list_json
from users.models import TruffeUser

import json


@login_required
def membership_add(request, pk):
    from members.models import MemberSet

    memberset = get_object_or_404(MemberSet, pk=pk)
    if not memberset.rights_can('EDIT', request.user):
        raise Http404

    done = False
    if request.method == 'POST':
        form = MembershipAddForm(request.user, request.POST, group=memberset)

        if form.is_valid():
            membership = form.save(commit=False)
            membership.group = memberset

            # Try to find the user. If he dosen't exists, create it.
            try:
                user = TruffeUser.objects.get(username=form.cleaned_data['user'])
            except TruffeUser.DoesNotExist:
                user = TruffeUser()
                user.username = form.cleaned_data['user']
                user.last_name, user.first_name, user.email = get_attrs_of_sciper(user.username)
                user.is_active = True
                user.save()

            membership.user = user
            membership.save()

            membership.user.clear_rights_cache()

            messages.success(request, _(u'Membre ajouté !'))

            done = True

    else:
        form = MembershipAddForm(request.user, group=memberset)

    return render(request, 'members/membership/add.html', {'form': form, 'done': done, 'group': memberset})


@login_required
def membership_delete(request, pk):
    """Delete a membership"""
    from members.models import Membership

    membership = get_object_or_404(Membership, pk=pk)

    if not membership.group.rights_can('DELETE', request.user):
        raise Http404

    if request.method == 'POST':
        membership.end_date = now()
        membership.save()

        messages.success(request, _(u'Membre retiré !'))

        return redirect('members.views.memberset_show', membership.group.pk)

    return render(request, 'members/membership/delete.html', {'membership': membership})


@login_required
def membership_toggle_fees(request, pk):
    from members.models import Membership

    membership = get_object_or_404(Membership, pk=pk)

    if not membership.group.rights_can('EDIT', request.user):
        raise Http404

    membership.payed_fees = not membership.payed_fees
    membership.save()

    messages.success(request, _(u'Cotisation mise à jour !'))

    return redirect('members.views.memberset_show', membership.group.pk)


@login_required
@csrf_exempt
def membership_list_json(request, pk):
    """Display the list of members, json call for the list"""
    from members.models import MemberSet, Membership

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    unit = get_current_unit(request)

    # Get the MemberSet
    memberset = get_object_or_404(MemberSet, pk=pk)

    # Check unit access
    if not memberset.rights_can('SHOW', request.user):
        raise Http404

    # Filter by group and check they are still in the group
    filter2 = lambda x: x.filter(group=memberset, end_date=None)

    return generic_list_json(request, Membership, ['user', 'start_date', 'payed_fees', 'group', 'pk'], 'members/membership/list_json.html', bonus_data={'handle_fees': memberset.handle_fees}, filter_fields=['user__first_name', 'user__last_name', 'user__username'], bonus_filter_function=filter2)


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
