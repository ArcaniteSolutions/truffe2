# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from app.ldaputils import get_attrs_of_sciper
from app.utils import update_current_unit
from members.forms2 import MembershipAddForm, MembershipImportForm
from generic.datatables import generic_list_json
from users.models import TruffeUser

import json
import re
import string


@login_required
def membership_add(request, pk):
    from members.models import MemberSet, MemberSetLogging

    memberset = get_object_or_404(MemberSet, pk=pk)
    if not memberset.rights_can('EDIT', request.user):
        raise Http404

    done = False
    done_user = None

    if request.method == 'POST':
        form = MembershipAddForm(request.user, memberset, request.POST)

        if form.is_valid():
            # Try to find the user. If he dosen't exists, create it.
            try:
                user = TruffeUser.objects.get(username=form.cleaned_data['user'])
            except TruffeUser.DoesNotExist:
                user = TruffeUser(username=form.cleaned_data['user'], is_active=True)
                user.last_name, user.first_name, user.email = get_attrs_of_sciper(user.username)
                user.save()

            if memberset.membership_set.filter(user=user).count():
                pass
            else:
                membership = form.save(commit=False)
                membership.group = memberset
                membership.user = user
                membership.save()

                MemberSetLogging(who=request.user, what='edited', object=memberset, extra_data='{"edited": {"%s": ["None", "Membre"]}}' % (user.get_full_name(),)).save()

                done_user = user

            done = True
            form = MembershipAddForm(request.user, memberset)

    else:
        form = MembershipAddForm(request.user, memberset)

    return render(request, 'members/membership/add.html', {'form': form, 'done': done, 'done_user': done_user, 'group': memberset})


@login_required
def membership_delete(request, pk):
    """Delete a membership"""
    from members.models import Membership, MemberSetLogging

    membership = get_object_or_404(Membership, pk=pk)

    if not membership.group.rights_can('DELETE', request.user):
        raise Http404

    if request.method == 'POST':
        membership.end_date = now()
        membership.save()

        MemberSetLogging(who=request.user, what='edited', object=membership.group, extra_data='{"edited": {"%s": ["Membre", "None"]}}' % (membership.user.get_full_name(),)).save()
        messages.success(request, _(u'Membre retiré !'))

        return redirect('members.views.memberset_show', membership.group.pk)

    return render(request, 'members/membership/delete.html', {'membership': membership})


@login_required
def membership_toggle_fees(request, pk):
    from members.models import Membership, MemberSetLogging

    membership = get_object_or_404(Membership, pk=pk)

    if not membership.group.rights_can('EDIT', request.user):
        raise Http404

    membership.payed_fees = not membership.payed_fees
    membership.save()

    MemberSetLogging(who=request.user, what='edited', object=membership.group,
                     extra_data='{"edited": {"Cotisation %s": ["%s ", "%s"]}}' % (membership.user.get_full_name(), not membership.payed_fees, membership.payed_fees)).save()
    messages.success(request, _(u'Cotisation mise à jour !'))

    return redirect('members.views.memberset_show', membership.group.pk)


@login_required
@csrf_exempt
def membership_list_json(request, pk):
    """Display the list of members, json call for the list"""
    from members.models import MemberSet, Membership

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    # Get the MemberSet
    memberset = get_object_or_404(MemberSet, pk=pk)

    # Check user access
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

    list_users = map(lambda mship: (mship.user.username, mship.payed_fees), memberset.membership_set.filter(end_date=None))

    response = HttpResponse(json.dumps(list_users), mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=export_%s_%s.json' % (filter(lambda x: x in string.ascii_letters + string.digits, memberset.name), filter(lambda x: x in string.ascii_letters + string.digits + '._', str(now())),)
    return response


@login_required
def import_members(request, pk):
    from members.models import MemberSet, Membership, MemberSetLogging

    memberset = get_object_or_404(MemberSet, pk=pk)
    if not memberset.rights_can('EDIT', request.user):
        raise Http404

    logs = []

    if request.method == 'POST':
        form = MembershipImportForm(request.user, memberset, request.POST, request.FILES)

        if form.is_valid():

            edition_extra_data = {}
            try:
                imp_file = json.loads(request.FILES['imported'].read())
                for user_data in imp_file:
                    if isinstance(user_data, (int, str, unicode)):
                        username = str(user_data)
                        fees = False
                    elif type(user_data) is list:
                        username = user_data[0]
                        fees = len(user_data) > 1 and user_data[1]
                    else:
                        continue

                    try:
                        user = TruffeUser.objects.get(username=username)
                    except TruffeUser.DoesNotExist:
                        if re.match('^\d{6}$', username):
                            user = TruffeUser(username=username, is_active=True)
                            user.last_name, user.first_name, user.email = get_attrs_of_sciper(username)
                            user.save()
                        else:
                            logs.append(('danger', username, _(u'Impossible de créer l\'utilisateur')))
                            user = None

                    if user:
                        if memberset.membership_set.filter(user=user).count():
                            logs.append(('warning', user, _(u'L\'utilisateur est déjà membre de ce groupe')))
                        else:
                            # Copy the fees status if asked
                            payed_fees = form.cleaned_data.get('copy_fees_status', False) and fees
                            Membership(group=memberset, user=user, payed_fees=payed_fees).save()
                            logs.append(('success', user, _(u'Utilisateur ajouté avec succès')))
                            edition_extra_data[user.get_full_name()] = ["None", "Membre"]
                MemberSetLogging(who=request.user, what='edited', object=memberset, extra_data='{"edited": %s}' % (json.dumps(edition_extra_data),)).save()
            except ValueError:
                logs.append(('danger', _(u'ERREUR'), _(u'Le fichier ne peut pas être lu correctement, l\'import a été annulé')))

    else:
        form = MembershipImportForm(request.user, memberset)

    logs.sort(key=lambda x: x[0])
    return render(request, 'members/membership/import.html', {'form': form, 'logs': logs, 'group': memberset, 'display_list_panel': True})
