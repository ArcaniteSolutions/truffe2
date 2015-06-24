# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.encoding import smart_str
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db import connections
from django.core.paginator import InvalidPage, EmptyPage, Paginator, PageNotAnInteger
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

from generic.datatables import generic_list_json

from units.models import Accreditation, AccreditationLog
from app.utils import update_current_unit, get_current_unit
from app.ldaputils import get_attrs_of_sciper
from users.models import TruffeUser


@login_required
def accreds_list(request):
    """Display the list of accreds"""

    from units.models import Unit

    main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

    main_unit.set_rights_can_select(lambda unit: Accreditation.static_rights_can('LIST', request.user, unit))
    main_unit.set_rights_can_edit(lambda unit: Accreditation.static_rights_can('CREATE', request.user, unit))
    main_unit.check_if_can_use_hidden(request.user)

    if request.GET.get('upk'):
        update_current_unit(request, request.GET.get('upk'))

    can_edit = Accreditation.static_rights_can('CREATE', request.user, get_current_unit(request))

    return render(request, 'units/accreds/list.html', {'main_unit': main_unit, 'can_edit': can_edit})


@login_required
@csrf_exempt
def accreds_list_json(request):
    """Display the list of accreds, json call for the list"""

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    unit = get_current_unit(request)

    # Check unit access
    if not Accreditation.static_rights_can('LIST', request.user, unit):
        raise Http404

    # Filter by unit
    filter_ = lambda x: x.filter(unit=unit)

    # Si pas le droit de créer, filtrage des accreds invisibles
    if not Accreditation.static_rights_can('CREATE', request.user, get_current_unit(request)):
        filter__ = lambda x: x.filter(hidden_in_truffe=False)
    else:
        filter__ = lambda x: x

    # Filter old accreds, if needed
    if request.GET.get('h', '0') == '0':
        filter2 = lambda x: filter_(filter__(x)).filter(end_date=None)
    else:
        filter2 = lambda x: filter_(filter__(x))

    return generic_list_json(request, Accreditation, ['pk', 'user', 'get_role_or_display_name', 'start_date', 'no_epfl_sync', 'hidden_in_epfl', 'hidden_in_truffe', 'renewal_date', 'pk'], 'units/accreds/list_json.html', filter_fields=['user__first_name', 'user__last_name', 'role__name'], bonus_filter_function=filter2, columns_mapping={'get_role_or_display_name': 'role__name', 'user': 'user__first_name'})


@login_required
def accreds_logs_list(request):
    """Display the list of accreds"""

    from units.models import Unit

    main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

    main_unit.set_rights_can_select(lambda unit: Accreditation.static_rights_can('LIST', request.user, unit))
    main_unit.set_rights_can_edit(lambda unit: Accreditation.static_rights_can('CREATE', request.user, unit))
    main_unit.check_if_can_use_hidden(request.user)

    if request.GET.get('upk'):
        update_current_unit(request, request.GET.get('upk'))

    return render(request, 'units/accreds/logs_list.html', {'main_unit': main_unit})


@login_required
@csrf_exempt
def accreds_logs_list_json(request):
    """Display the list of accreds, json call for the list"""

    # Update current unit
    update_current_unit(request, request.GET.get('upk'))

    unit = get_current_unit(request)

    # Check unit access
    if not Accreditation.static_rights_can('LIST', request.user, unit):
        raise Http404

    # Filter by unit
    filter_ = lambda x: x.filter(accreditation__unit=unit)

    # Si pas le droit de créer, filtrage des accreds invisibles
    if not Accreditation.static_rights_can('CREATE', request.user, get_current_unit(request)):
        filter__ = lambda x: x.filter(accreditation__hidden_in_truffe=False)
    else:
        filter__ = lambda x: x

    filter2 = lambda x: filter_(filter__(x))

    return generic_list_json(request, AccreditationLog, ['pk', 'accreditation__user', 'type', 'when', 'what'], 'units/accreds/logs_list_json.html', filter_fields=['accred__user__first_name', 'accreditation__user__last_name', 'accreditation__role__name', 'who__first_name', 'who__last_name'], bonus_filter_function=filter2, columns_mapping={'pk': 'accreditation__user__first_name'})


@login_required
def accreds_renew(request, pk):
    """Renew an accreds"""

    accreds = [get_object_or_404(Accreditation, pk=pk_, end_date=None) for pk_ in filter(lambda x: x, pk.split(','))]

    multi_obj = len(accreds) > 1

    for accred in accreds:
        if not accred.rights_can('EDIT', request.user):
            raise Http404

    if request.method == 'POST':
        for accred in accreds:
            accred.renewal_date = now()
            accred.save()

            AccreditationLog(accreditation=accred, who=request.user, type='renewed').save()

        if multi_obj:
            messages.success(request, _(u'Accréditations renouvelées !'))
        else:
            messages.success(request, _(u'Accréditation renouvelée !'))

        return redirect('units.views.accreds_list')

    return render(request, 'units/accreds/renew.html', {'accreds': accreds, 'multi_obj': multi_obj})


@login_required
def accreds_edit(request, pk):

    accred = get_object_or_404(Accreditation, pk=pk)

    base_role = accred.role
    old_accred_data = accred.__dict__.copy()

    if not accred.rights_can('EDIT', request.user):
        raise Http404

    from units.forms2 import AccreditationEditForm

    done = False
    cannot_last_prez = False

    if request.method == 'POST':  # If the form has been submitted...
        form = AccreditationEditForm(request.POST, instance=accred)

        if form.is_valid():  # If the form is valid

            if base_role.pk == settings.PRESIDENT_ROLE_PK and not accred.rights_can('INGORE_PREZ', request.user) and accred.unit.accreditation_set.filter(role__pk=settings.PRESIDENT_ROLE_PK, end_date=None).count() <= 1 and form.cleaned_data['role'].pk != settings.PRESIDENT_ROLE_PK:
                cannot_last_prez = True
            else:

                accred = form.save(commit=False)

                if accred.role.pk != base_role.pk:
                    # On termine l'accrédiation
                    accred.end_date = now()
                    accred.save()

                    AccreditationLog(accreditation=accred, who=request.user, type='deleted').save()

                    # Et on clone la nouvelle
                    accred.pk = None
                    accred.end_date = None

                    accred.save()
                    accred.check_if_validation_needed(request)

                    AccreditationLog(accreditation=accred, who=request.user, type='created').save()

                else:
                    changes = ""  # NB: Pas traduit, au cas ou besion de parsing

                    if accred.display_name != old_accred_data['display_name']:
                        changes += "DisplayName \"%s\" -> \"%s\"\n" % (old_accred_data['display_name'], accred.display_name,)

                    if accred.no_epfl_sync != old_accred_data['no_epfl_sync']:
                        if accred.no_epfl_sync:
                            changes += 'Now NoEpflSync\n'
                        else:
                            changes += 'Now EpflSync\n'

                    if accred.hidden_in_epfl != old_accred_data['hidden_in_epfl']:
                        if accred.hidden_in_epfl:
                            changes += 'Now EpflHidden\n'
                        else:
                            changes += 'Now EpflShown\n'

                    if accred.hidden_in_truffe != old_accred_data['hidden_in_truffe']:
                        if accred.hidden_in_truffe:
                            changes += 'Now TruffeHidden\n'
                        else:
                            changes += 'Now TruffeShown\n'

                    AccreditationLog(accreditation=accred, who=request.user, type='edited', what=changes).save()

                accred.save()

                accred.user.clear_rights_cache()

                messages.success(request, _(u'Accréditation sauvegardée !'))

                done = True

    else:
        form = AccreditationEditForm(instance=accred)

    return render(request, 'units/accreds/edit.html', {'form': form, 'done': done, 'cannot_last_prez': cannot_last_prez})


@login_required
def accreds_delete(request, pk):
    """Delete an accred"""

    accreds = [get_object_or_404(Accreditation, pk=pk_, end_date=None) for pk_ in filter(lambda x: x, pk.split(','))]

    multi_obj = len(accreds) > 1

    cannot_last_prez = False
    cannot_last_prez_accred = None

    for accred in accreds:

        if not accred.rights_can('DELETE', request.user):
            raise Http404

        if accred.role.pk == settings.PRESIDENT_ROLE_PK and not accred.rights_can('INGORE_PREZ', request.user) and accred.unit.accreditation_set.filter(role__pk=settings.PRESIDENT_ROLE_PK, end_date=None).count() <= 1:
            cannot_last_prez = True
            cannot_last_prez_accred = accred

    if not cannot_last_prez and request.method == 'POST':

        for accred in accreds:
            accred.end_date = now()
            accred.save()

            AccreditationLog(accreditation=accred, who=request.user, type='deleted').save()

            accred.user.clear_rights_cache()

        if multi_obj:
            messages.success(request, _(u'Accréditations supprimées !'))
        else:
            messages.success(request, _(u'Accréditation supprimée !'))

        return redirect('units.views.accreds_list')

    return render(request, 'units/accreds/delete.html', {'accreds': accreds, 'cannot_last_prez': cannot_last_prez, 'multi_obj': multi_obj, 'cannot_last_prez_accred': cannot_last_prez_accred})


@login_required
def accreds_validate(request, pk):
    """Validate an accred"""

    accreds = [get_object_or_404(Accreditation, pk=pk_, end_date=None) for pk_ in filter(lambda x: x, pk.split(','))]

    multi_obj = len(accreds) > 1

    for accred in accreds:
        if not accred.rights_can('VALIDATE', request.user):
            raise Http404

    if request.method == 'POST':

        for accred in accreds:
            accred.need_validation = False
            accred.save()

            accred.user.clear_rights_cache()

            AccreditationLog(accreditation=accred, who=request.user, type='validated').save()

            from notifications.utils import notify_people
            dest_users = accred.unit.users_with_access('ACCREDITATION', no_parent=True)
            notify_people(request, 'Accreds.Validated', 'accreds_validated', accred, dest_users)

        if multi_obj:
            messages.success(request, _(u'Accréditations validées !'))
        else:
            messages.success(request, _(u'Accréditation validée !'))

        return redirect('units.views.accreds_list')

    return render(request, 'units/accreds/validate.html', {'accreds': accreds, 'multi_obj': multi_obj})


@login_required
def accreds_add(request):

    update_current_unit(request, request.GET.get('upk'))
    unit = get_current_unit(request)

    if not Accreditation.static_rights_can('CREATE', request.user, unit):
        raise Http404

    from units.forms2 import AccreditationAddForm

    done = False

    if request.method == 'POST':  # If the form has been submitted...
        form = AccreditationAddForm(request.user, request.POST)

        if form.is_valid():  # If the form is valid
            accred = form.save(commit=False)

            accred.unit = unit

            # Try to find the user. If he dosen't exists, create it.
            try:
                user = TruffeUser.objects.get(username=form.cleaned_data['user'].strip())
            except TruffeUser.DoesNotExist:
                user = TruffeUser()

                user.username = form.cleaned_data['user'].strip()

                user.last_name, user.first_name, user.email = get_attrs_of_sciper(user.username)

                user.is_active = True

                user.save()

            accred.user = user
            accred.save()

            AccreditationLog(accreditation=accred, who=request.user, type='created').save()

            # Check if validation is needed
            accred.check_if_validation_needed(request)
            accred.save()

            accred.user.clear_rights_cache()

            messages.success(request, _(u'Accréditation sauvegardée !'))

            done = True

    else:
        form = AccreditationAddForm(request.user)

    return render(request, 'units/accreds/add.html', {'form': form, 'done': done, 'unit': unit})
