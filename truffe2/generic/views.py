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
from django.db.models import Max, Q


import json
import datetime
import pytz


from generic.datatables import generic_list_json
from generic.forms import ContactForm
from app.utils import update_current_unit, get_current_unit, update_current_year, get_current_year, send_templated_mail
from rights.utils import BasicRightModel


def get_unit_data(model_class, request, allow_blank=True):

    from generic.models import GenericExternalUnitAllowed

    unit_mode = hasattr(model_class.MetaData, 'has_unit') and model_class.MetaData.has_unit
    unit_blank = allow_blank and unit_mode and issubclass(model_class, GenericExternalUnitAllowed)

    current_unit = None

    if unit_mode:

        if request.GET.get('upk'):
            update_current_unit(request, request.GET.get('upk'))

        if request.POST.get('upk'):
            update_current_unit(request, request.POST.get('upk'))

        current_unit = get_current_unit(request, unit_blank)

    return unit_mode, current_unit, unit_blank


def get_year_data(model_class, request):

    from accounting_core.utils import AccountingYearLinked
    from accounting_core.models import AccountingYear

    year_mode = issubclass(model_class, AccountingYearLinked)
    current_year = None

    if year_mode:

        if request.GET.get('ypk'):
            update_current_year(request, request.GET.get('ypk'))

        if request.POST.get('ypk'):
            update_current_year(request, request.POST.get('ypk'))

        current_year = get_current_year(request)

    return year_mode, current_year, AccountingYear


def generate_generic_list(module, base_name, model_class, json_view_suffix, right_to_check, right_to_check_edit, template_to_use, allow_blank, object_filter=False):

    @login_required
    def _generic_generic_list(request):

        json_view = module.__name__ + '.views.' + base_name + json_view_suffix
        edit_view = module.__name__ + '.views.' + base_name + '_edit'
        show_view = module.__name__ + '.views.' + base_name + '_show'
        deleted_view = module.__name__ + '.views.' + base_name + '_deleted'
        status_view = module.__name__ + '.views.' + base_name + '_switch_status'

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_blank=allow_blank)
        main_unit = None

        if unit_mode:
            from units.models import Unit

            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

            main_unit.set_rights_can_select(lambda unit: model_class.static_rights_can(right_to_check, request.user, unit, current_year))
            main_unit.set_rights_can_edit(lambda unit: model_class.static_rights_can(right_to_check_edit, request.user, unit, current_year))
        else:
            # The LIST right is not verified here if we're in unit mode. We
            # need to test (in the view) in another unit is available for LIST
            # if the current unit isn't !
            if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can(right_to_check, request.user, current_unit, current_year):
                raise Http404

        if hasattr(model_class, 'moderable_object') and model_class.moderable_object:  # If the object is moderable, list all moderable things by the current user
            # List all moderiables in the 'todo' satate
            moderables = model_class.objects.filter(status=model_class.moderable_state)

            # Filter to check if user has rights
            moderables = filter(lambda m: m.rights_can('VALIDATE', request.user), moderables)
        else:
            moderables = False

        if object_filter:
            objects = model_class.get_linked_object_class().objects.filter(unit=current_unit)
        else:
            objects = []

        return render(request, [module.__name__ + '/' + base_name + '/%s.html' % (template_to_use,), 'generic/generic/%s.html' % (template_to_use,)], {
            'Model': model_class, 'json_view': json_view, 'edit_view': edit_view, 'deleted_view': deleted_view, 'show_view': show_view, 'status_view': status_view,
            'unit_mode': unit_mode, 'main_unit': main_unit, 'unit_blank': unit_blank,
            'year_mode': year_mode, 'years_available': AccountingYear.build_year_menu('LIST', request.user),
            'moderables': moderables, 'object_filter': objects,
        })

    return _generic_generic_list


def generate_list(module, base_name, model_class):

    return generate_generic_list(module, base_name, model_class, '_list_json', 'LIST', 'CREATE', 'list', True)


def generate_list_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generic_list_json(request):
        show_view = module.__name__ + '.views.' + base_name + '_show'
        edit_view = module.__name__ + '.views.' + base_name + '_edit'
        delete_view = module.__name__ + '.views.' + base_name + '_delete'
        logs_view = module.__name__ + '.views.' + base_name + '_logs'

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        if unit_mode:
            if not current_unit:
                if request.user.is_superuser:  # Never filter
                    filter_ = lambda x: x.filter(unit=None)
                else:
                    filter_ = lambda x: x.filter(unit=None, unit_blank_user=request.user)
            else:
                filter_ = lambda x: x.filter(unit=current_unit)
        else:
            filter_ = lambda x: x

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('LIST', request.user, current_unit, current_year):
            raise Http404

        return generic_list_json(request, model_class, [col for (col, disp) in model_class.MetaData.list_display] + ['pk'], [module.__name__ + '/' + base_name + '/list_json.html', 'generic/generic/list_json.html'],
            {'Model': model_class,
             'show_view': show_view,
             'edit_view': edit_view,
             'delete_view': delete_view,
             'logs_view': logs_view,
             'list_display': model_class.MetaData.list_display,
            },
            True, model_class.MetaData.filter_fields,
            bonus_filter_function=filter__,
            selector_column=True,
        )

    return _generic_list_json


def generate_list_related(module, base_name, model_class):

    return generate_generic_list(module, base_name, model_class, '_list_related_json', 'VALIDATE', 'VALIDATE', 'list_related', False, True)


def generate_list_related_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generic_list_json(request):
        show_view = module.__name__ + '.views.' + base_name + '_show'
        edit_view = module.__name__ + '.views.' + base_name + '_edit'
        delete_view = module.__name__ + '.views.' + base_name + '_delete'
        logs_view = module.__name__ + '.views.' + base_name + '_logs'

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_blank=False)

        if unit_mode:
            filter_ = lambda x: x.filter(**{model_class.MetaState.unit_field.replace('.', '__'): current_unit})
        else:
            filter_ = lambda x: x

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        def filter_object(qs, request):
            if request.POST.get('sSearch_0'):
                return qs.filter(**{'__'.join(model_class.MetaState.unit_field.split('.')[:-1] + ['pk']): request.POST.get('sSearch_0'), model_class.MetaState.unit_field.replace('.', '__'): current_unit})
            else:
                return qs

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('VALIDATE', request.user, current_unit, current_year):
            raise Http404

        return generic_list_json(request, model_class, [col for (col, disp) in model_class.MetaData.list_display_related] + ['pk'], [module.__name__ + '/' + base_name + '/list_related_json.html', 'generic/generic/list_related_json.html'],
            {'Model': model_class,
             'show_view': show_view,
             'edit_view': edit_view,
             'delete_view': delete_view,
             'logs_view': logs_view,
             'list_display': model_class.MetaData.list_display_related,
             'upk_noswitch': True, 'from_related': True,
            },
            True, model_class.MetaData.filter_fields,
            bonus_filter_function=filter__,
            bonus_filter_function_with_parameters=filter_object,
            deca_one_status=True,
            selector_column=True,
        )

    return _generic_list_json


def generate_edit(module, base_name, model_class, form_class, log_class):

    @login_required
    @csrf_exempt
    def _generic_edit(request, pk):
        list_view = module.__name__ + '.views.' + base_name + '_list'
        list_related_view = module.__name__ + '.views.' + base_name + '_list_related'
        show_view = module.__name__ + '.views.' + base_name + '_show'

        related_mode = request.GET.get('_fromrelated') == '_'

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        try:
            obj = model_class.objects.get(pk=pk, deleted=False)

            if unit_mode:
                update_current_unit(request, obj.unit.pk if obj.unit else -1)
                current_unit = obj.unit

            if year_mode:
                update_current_year(request, obj.accounting_year.pk)
                current_year = obj.accounting_year

            if isinstance(obj, BasicRightModel) and not obj.rights_can('EDIT', request.user):
                raise Http404

        except (ValueError, model_class.DoesNotExist):
            obj = model_class()

            if unit_mode:
                if unit_blank and not current_unit:
                    obj.unit_blank_user = request.user
                obj.unit = current_unit

            if year_mode:

                # Est-ce qu'on va tenter de créer un truc dans une année
                # comptable pas possible ?
                if current_year not in AccountingYear.build_year_menu('CREATE', request.user):
                    update_current_year(request, None)
                    ___, current_year, ___ = get_year_data(model_class, request)

                obj.accounting_year = current_year

            if isinstance(obj, BasicRightModel) and not obj.rights_can('CREATE', request.user):
                raise Http404

        if unit_mode:
            from units.models import Unit

            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

            main_unit.set_rights_can_select(lambda unit: model_class.static_rights_can('CREATE', request.user, unit, current_year))
            main_unit.set_rights_can_edit(lambda unit: model_class.static_rights_can('CREATE', request.user, unit, current_year))
        else:
            main_unit = None

        if obj.pk:
            before_data = obj.build_state()
        else:
            before_data = None

        if request.method == 'POST':  # If the form has been submitted...
            form = form_class(request.user, request.POST, request.FILES, instance=obj)

            if form.is_valid():  # If the form is valid

                obj = form.save()

                if isinstance(obj, BasicRightModel):
                    obj.rights_expire()

                if hasattr(obj, 'save_signal'):
                    obj.save_signal()

                messages.success(request, _(u'Élément sauvegardé !'))

                if not before_data:
                    log_class(who=request.user, what='created', object=obj).save()
                else:
                    # Compute diff
                    after_data = obj.build_state()

                    for key in list(before_data)[::]:  # Be sure we're on a copy
                        if key in after_data and after_data[key] == before_data[key]:
                            del after_data[key]
                            del before_data[key]

                    added = {}
                    edited = {}
                    deleted = {}

                    for key in before_data:
                        if key not in after_data:
                            deleted[key] = before_data[key]
                        else:
                            if not after_data[key]:
                                deleted[key] = before_data[key]
                                del after_data[key]
                            elif before_data[key]:
                                edited[key] = (before_data[key], after_data[key])
                                del after_data[key]

                    added = after_data

                    diff = {'added': added, 'edited': edited, 'deleted': deleted}

                    log_class(who=request.user, what='edited', object=obj, extra_data=json.dumps(diff)).save()

                if request.POST.get('post-save-dest'):
                    if request.POST.get('post-save-dest') == 'new':
                        return redirect(module.__name__ + '.views.' + base_name + '_edit', pk='~')
                    else:
                        return redirect(module.__name__ + '.views.' + base_name + '_edit', pk=obj.pk)

                return HttpResponseRedirect('%s%s' % (reverse(module.__name__ + '.views.' + base_name + '_show', args=(obj.pk,)), '?_upkns=_&_fromrelated=_' if related_mode else ''))
        else:
            form = form_class(request.user, instance=obj)

        return render(request, [module.__name__ + '/' + base_name + '/edit.html', 'generic/generic/edit.html'], {'Model': model_class, 'form': form, 'list_view': list_view, 'show_view': show_view,
                                                                                                                 'unit_mode': unit_mode, 'current_unit': current_unit, 'main_unit': main_unit, 'unit_blank': unit_mode,
          'year_mode': year_mode, 'current_year': current_year, 'years_available': AccountingYear.build_year_menu('EDIT' if obj.pk else 'CREATE', request.user),
                                                                                                                 'related_mode': related_mode, 'list_related_view': list_related_view})

    return _generic_edit


def generate_show(module, base_name, model_class, log_class):

    @login_required
    def _generic_show(request, pk):

        edit_view = module.__name__ + '.views.' + base_name + '_edit'
        delete_view = module.__name__ + '.views.' + base_name + '_delete'
        log_view = module.__name__ + '.views.' + base_name + '_log'
        list_view = module.__name__ + '.views.' + base_name + '_list'
        list_related_view = module.__name__ + '.views.' + base_name + '_list_related'
        status_view = module.__name__ + '.views.' + base_name + '_switch_status'
        contact_view = module.__name__ + '.views.' + base_name + '_contact'

        related_mode = request.GET.get('_fromrelated') == '_'

        obj = get_object_or_404(model_class, pk=pk, deleted=False)

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        if unit_mode:
            update_current_unit(request, obj.unit.pk if obj.unit else -1)
            current_unit = obj.unit

        if year_mode:
            update_current_year(request, obj.accounting_year.pk)
            current_year = obj.accounting_year

        if isinstance(obj, BasicRightModel) and not obj.rights_can('SHOW', request.user):
            raise Http404

        rights = []

        if hasattr(model_class, 'MetaRights'):

            for key, info in obj.MetaRights.rights.iteritems():
                rights.append((key, info, obj.rights_can(key, request.user)))

        log_entires = log_class.objects.filter(object=obj).order_by('-when').all()

        if hasattr(obj, 'contactables_groups'):
            contactables_groups = obj.contactables_groups()
        else:
            contactables_groups = None

        return render(request, [module.__name__ + '/' + base_name + '/show.html', 'generic/generic/show.html'], {
            'Model': model_class, 'delete_view': delete_view, 'edit_view': edit_view, 'log_view': log_view, 'list_view': list_view, 'status_view': status_view, 'contact_view': contact_view, 'list_related_view': list_related_view,
            'obj': obj, 'log_entires': log_entires,
            'rights': rights,
            'unit_mode': unit_mode, 'current_unit': current_unit,
            'year_mode': year_mode, 'current_year': current_year,
            'contactables_groups': contactables_groups,
            'related_mode': related_mode,
        })

    return _generic_show


def generate_delete(module, base_name, model_class, log_class):

    @login_required
    def _generic_delete(request, pk):

        show_view = module.__name__ + '.views.' + base_name + '_show'
        list_view = module.__name__ + '.views.' + base_name + '_list'
        list_related_view = module.__name__ + '.views.' + base_name + '_list_related'

        related_mode = request.GET.get('_fromrelated') == '_'

        objs = [get_object_or_404(model_class, pk=pk_, deleted=False) for pk_ in filter(lambda x: x, pk.split(','))]

        multi_obj = len(objs) > 1

        for obj in objs:
            unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)
            year_mode, current_year, AccountingYear = get_year_data(model_class, request)
            if unit_mode:
                update_current_unit(request, obj.unit.pk if obj.unit else -1)

            if year_mode:
                update_current_year(request, obj.accounting_year.pk)

            if isinstance(obj, BasicRightModel) and not obj.rights_can('DELETE', request.user):
                raise Http404

        can_delete = True
        can_delete_message = ''
        prob_obj = None

        for obj in objs:
            if hasattr(obj, 'can_delete'):
                (can_delete, can_delete_message) = obj.can_delete()

                if not can_delete:
                    prob_obj = obj

        if can_delete and request.method == 'POST' and request.POST.get('do') == 'it':

            for obj in objs:
                obj.deleted = True
                if hasattr(obj, 'delete_signal'):
                    obj.delete_signal()
                obj.save()

                log_class(who=request.user, what='deleted', object=obj).save()

                messages.success(request, _(u'Élément supprimé !'))

            if related_mode:
                return redirect(list_related_view)
            else:
                return redirect(list_view)

        return render(request, [module.__name__ + '/' + base_name + '/delete.html', 'generic/generic/delete.html'], {
            'Model': model_class, 'show_view': show_view, 'list_view': list_view, 'list_related_view': list_related_view,
            'objs': objs, 'can_delete': can_delete, 'can_delete_message': can_delete_message,
            'related_mode': related_mode, 'multi_obj': multi_obj, 'prob_obj': prob_obj
        })

    return _generic_delete


def generate_deleted(module, base_name, model_class, log_class):

    @login_required
    def _generic_deleted(request):

        list_view = module.__name__ + '.views.' + base_name + '_list'

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('RESTORE', request.user, current_unit, current_year):
            raise Http404

        if unit_mode:
            from units.models import Unit

            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

            main_unit.set_rights_can_select(lambda unit: model_class.static_rights_can('RESTORE', request.user, unit, current_year))
            main_unit.set_rights_can_edit(lambda unit: model_class.static_rights_can('RESTORE', request.user, unit, current_year))
        else:
            main_unit = None

        if request.method == 'POST':
            obj = get_object_or_404(model_class, pk=request.POST.get('pk'), deleted=True)

            if unit_mode:
                update_current_unit(request, obj.unit.pk if obj.unit else -1)
            if year_mode:
                update_current_year(request, obj.accounting_year.pk)

            if isinstance(obj, BasicRightModel) and not obj.rights_can('RESTORE', request.user):
                raise Http404

            obj.deleted = False
            if hasattr(obj, 'restore_signal'):
                obj.restore_signal()
            obj.save()

            log_class(who=request.user, what='restored', object=obj).save()

            messages.success(request, _(u'Élément restauré !'))
            return redirect(list_view)

        liste = model_class.objects.filter(deleted=True).annotate(Max('logs__when')).order_by('-logs__when__max')

        if unit_mode:
            liste = liste.filter(unit=current_unit)

        if year_mode:
            liste = liste.filter(accounting_year=current_year)
        else:
            liste = liste.all()

        return render(request, [module.__name__ + '/' + base_name + '/deleted.html', 'generic/generic/deleted.html'], {
            'Model': model_class, 'list_view': list_view, 'liste': liste,
            'unit_mode': unit_mode, 'current_unit': current_unit, 'main_unit': main_unit,
            'year_mode': year_mode, 'current_year': current_year, 'years_available': AccountingYear.build_year_menu('RESTORE', request.user),
        })

    return _generic_deleted


def generate_switch_status(module, base_name, model_class, log_class):

    @login_required
    def _switch_status(request, pk):

        objs = [get_object_or_404(model_class, pk=pk_, deleted=False) for pk_ in filter(lambda x: x, pk.split(','))]

        multi_obj = len(objs) > 1

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        # Don't switch when switching status
        # if unit_mode:
        #     update_current_unit(request, obj.unit.pk if obj.unit else -1)

        can_switch = True
        can_switch_message = ''
        done = False
        prob_obj = None
        no_more_access = False
        status_view = module.__name__ + '.views.' + base_name + '_switch_status'
        list_view = module.__name__ + '.views.' + base_name + '_list'

        dest_status = request.GET.get('dest_status')
        from_list = request.GET.get('from_list') == 'from_list'

        for obj in objs:
            if not hasattr(obj, 'MetaState') or dest_status not in obj.MetaState.states:
                raise Http404

            (can_switch, can_switch_message) = obj.can_switch_to(request.user, dest_status)

            if not can_switch:
                prob_obj = obj

        bonus_form = None

        if hasattr(model_class.MetaState, 'states_bonus_form'):
            bonus_form = model_class.MetaState.states_bonus_form.get(dest_status, None)

        if can_switch and request.method == 'POST' and request.POST.get('do') == 'it':

            for obj in objs:
                old_status = obj.status
                obj.status = dest_status
                obj.save()

                if isinstance(obj, BasicRightModel):
                    obj.rights_expire()

                if hasattr(obj, 'switch_status_signal'):
                    obj.switch_status_signal(request, old_status, dest_status)

                log_class(who=request.user, what='state_changed', object=obj, extra_data=json.dumps({'old': unicode(obj.MetaState.states.get(old_status)), 'new': unicode(obj.MetaState.states.get(dest_status))})).save()

                messages.success(request, _(u'Statut modifié !'))
                done = True
                no_more_access = not obj.rights_can('SHOW', request.user)

                if no_more_access:
                    messages.warning(request, _(u'Vous avez perdu le droit de voir l\'objet !'))

        return render(request, [module.__name__ + '/' + base_name + '/switch_status.html', 'generic/generic/switch_status.html'], {
            'Model': model_class, 'objs': objs, 'can_switch': can_switch, 'can_switch_message': can_switch_message, 'done': done, 'no_more_access': no_more_access,
            'dest_status': dest_status, 'dest_status_message': objs[0].MetaState.states.get(dest_status),
            'status_view': status_view, 'list_view': list_view,
            'bonus_form': bonus_form() if bonus_form else None,
            'from_list': from_list, 'multi_obj': multi_obj, 'prob_obj': prob_obj, 'pk': pk,
        })

    return _switch_status


def generate_contact(module, base_name, model_class, log_class):

    @login_required
    def _contact(request, pk, key):

        contact_view = module.__name__ + '.views.' + base_name + '_contact'
        show_view = module.__name__ + '.views.' + base_name + '_show'

        obj = get_object_or_404(model_class, pk=pk, deleted=False)

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)
        year_mode, current_year, AccountingYear = get_year_data(model_class, request)

        if unit_mode:
            update_current_unit(request, obj.unit.pk if obj.unit else -1)

        if year_mode:
            update_current_year(request, obj.accounting_year.pk)

        if isinstance(obj, BasicRightModel) and not obj.rights_can('SHOW', request.user):
            raise Http404

        if not hasattr(obj, 'contactables_groups'):
            raise Http404

        contactables_groups = obj.contactables_groups()

        done = False

        if request.method == 'POST':

            form = ContactForm(contactables_groups, request.POST)
            if form.is_valid():

                dest = [u.email for u in getattr(obj, 'build_group_members_for_%s' % (form.cleaned_data['key'],))()]

                context = {
                    'subject': form.cleaned_data['subject'],
                    'show_view': show_view,
                    'message': form.cleaned_data['message'],
                    'sender': request.user,
                    'obj': obj
                }

                send_templated_mail(request, _('Truffe :: Contact :: %s') % (form.cleaned_data['subject'],), request.user.email, dest, 'generic/generic/mail/contact', context)

                done = True
                messages.success(request, _(u'Message envoyé !'))
        else:
            form = ContactForm(contactables_groups, initial={'key': key})

        return render(request, [module.__name__ + '/' + base_name + '/contact.html', 'generic/generic/contact.html'], {
            'Model': model_class, 'obj': obj, 'contact_view': contact_view, 'form': form, 'done': done
        })

    return _contact


def check_unit_name(request):
    from units.models import Unit
    return HttpResponse(json.dumps({'result': 'ok' if Unit.objects.filter(name__icontains=request.GET.get('name')).count() == 0 else 'err'}))


def generate_calendar(module, base_name, model_class):

    return generate_generic_list(module, base_name, model_class, '_calendar_json', 'LIST', 'CREATE', 'calendar', True)


def generate_calendar_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generic_calendar_json(request):

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)
        year_mode, current_year, AccountingYear = get_year_data(model_class, request)

        if unit_mode:
            if not current_unit:
                if request.user.is_superuser:  # Never filter
                    filter_ = lambda x: x.filter(unit=None)
                else:
                    filter_ = lambda x: x.filter(unit=None, unit_blank_user=request.user)
            else:
                filter_ = lambda x: x.filter(unit=current_unit)
        else:
            filter_ = lambda x: x

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('LIST', request.user, current_unit, current_year):
            raise Http404

        start = request.GET.get('start')
        end = request.GET.get('end')

        start = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(start)))
        end = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(end)))

        liste = filter__(model_class.objects.filter((Q(start_date__gt=start) & Q(start_date__lt=end)) | (Q(end_date__gt=start) & Q(end_date__lt=end))).filter(Q(status='1_asking') | Q(status='2_online')))

        retour = []

        for l in liste:

            if l.status == '1_asking':
                icon = 'fa-question'
                className = ["event", "bg-color-redLight"]
            else:
                icon = 'fa-check'
                className = ["event", "bg-color-greenLight"]

            if l.rights_can('SHOW', request.user):
                url = l.display_url()
            else:
                url = ''

            titre = u'%s (%s)' % (l.get_linked_object(), l.get_linked_object().unit)

            retour.append({'title': titre, 'start': str(l.start_date), 'end': str(l.end_date), 'className': className, 'icon': icon, 'url': url, 'allDay': False, 'description': str(l)})

        return HttpResponse(json.dumps(retour))

    return _generic_calendar_json


def generate_calendar_related(module, base_name, model_class):

    return generate_generic_list(module, base_name, model_class, '_calendar_related_json', 'VALIDATE', 'VALIDATE', 'calendar_related', False, True)


def generate_calendar_related_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generic_calendar_related_json(request):

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_blank=False)
        year_mode, current_year, AccountingYear = get_year_data(model_class, request)

        if unit_mode:
            filter_ = lambda x: x.filter(**{model_class.MetaState.unit_field.replace('.', '__'): current_unit})
        else:
            filter_ = lambda x: x

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        if request.GET.get('filter_object'):
            filter___ = lambda x: x.filter(**{'__'.join(model_class.MetaState.unit_field.split('.')[:-1] + ['pk']): request.GET.get('filter_object'), model_class.MetaState.unit_field.replace('.', '__'): current_unit})
        else:
            filter___ = lambda x: x

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('VALIDATE', request.user, current_unit, current_year):
            raise Http404

        start = request.GET.get('start')

        end = request.GET.get('end')

        start = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(start)))
        end = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(end)))

        liste = filter___(filter__(model_class.objects.filter((Q(start_date__gt=start) & Q(start_date__lt=end)) | (Q(end_date__gt=start) & Q(end_date__lt=end))).filter(Q(status='1_asking') | Q(status='2_online'))))

        retour = []

        for l in liste:
            if l.unit:
                par = l.unit.name
            else:
                par = u'%s (%s)' % (l.unit_blank_name, l.unit_blank_user)

            if l.status == '1_asking':
                icon = 'fa-question'
                className = ["event", "bg-color-redLight"]
            else:
                icon = 'fa-check'
                className = ["event", "bg-color-greenLight"]

            if l.rights_can('SHOW', request.user):
                url = l.display_url()
            else:
                url = ''

            titre = u'%s (%s)' % (l.get_linked_object(), par)

            retour.append({'title': titre, 'start': str(l.start_date), 'end': str(l.end_date), 'className': className, 'icon': icon, 'url': url, 'allDay': False, 'description': str(l)})

        return HttpResponse(json.dumps(retour))

    return _generic_calendar_related_json


def generate_directory(module, base_name, model_class):

    @login_required
    def _generic_directory(request):

        if not model_class.static_rights_can('CREATE', request.user):
            raise Http404

        from units.models import Unit

        edit_view = module.__name__ + '.views.' + base_name + '_edit'

        units = model_class.get_linked_object_class().objects.order_by('unit__name').filter(deleted=False)

        if request.user.is_external():
            units = units.filter(allow_externals=True)

        units = [Unit.objects.get(pk=u['unit']) for u in units.values('unit').distinct()]

        for unit in units:
            unit.directory_objects = model_class.get_linked_object_class().objects.filter(unit=unit, deleted=False).order_by('title')

            if request.user.is_external():
                unit.directory_objects = unit.directory_objects.filter(allow_externals=True)

        return render(request, [module.__name__ + '/' + base_name + '/directory.html', 'generic/generic/directory.html'], {
            'Model': model_class, 'edit_view': edit_view,
            'units': units,
        })

    return _generic_directory
