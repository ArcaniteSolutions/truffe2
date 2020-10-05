# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db.models import Max, Q


from easy_thumbnails.files import get_thumbnailer
from jfu.http import upload_receive, UploadResponse, JFUResponse
import json
import datetime
import pytz
import uuid
import os
from sendfile import sendfile
import importlib
import copy
import inspect
import urllib
from wand.image import Image


from accounting_core.utils import CostCenterLinked
from generic.datatables import generic_list_json
from generic.forms import ContactForm
from app.utils import update_current_unit, get_current_unit, update_current_year, get_current_year, send_templated_mail, has_property, set_property
from rights.utils import BasicRightModel


def get_unit_data(model_class, request, allow_blank=True, allow_all_units=False):

    from generic.models import GenericExternalUnitAllowed

    unit_mode = hasattr(model_class.MetaData, 'has_unit') and model_class.MetaData.has_unit
    unit_blank = allow_blank and unit_mode and issubclass(model_class, GenericExternalUnitAllowed)

    current_unit = None

    if unit_mode:

        if request.GET.get('upk'):
            update_current_unit(request, request.GET.get('upk'))

        if request.POST.get('upk'):
            update_current_unit(request, request.POST.get('upk'))

        current_unit = get_current_unit(request, unit_blank, allow_all_units)

    if current_unit and current_unit.is_hidden:
        # Enpeche d'éventuel petit malins de trichers en mettant les IDs à la
        # main
        if not current_unit.check_if_can_use_hidden(request.user):
            raise Http404

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


def generate_generic_list(module, base_name, model_class, json_view_suffix, right_to_check, right_to_check_edit, template_to_use, allow_blank, object_filter=False, bonus_args_transformator=None, tag_class=None, allow_all_units=False):

    @login_required
    def _generic_generic_list(request, **bonus_args):

        json_view = '%s.views.%s%s' % (module.__name__, base_name, json_view_suffix)
        edit_view = '%s.views.%s_edit' % (module.__name__, base_name)
        show_view = '%s.views.%s_show' % (module.__name__, base_name)
        deleted_view = '%s.views.%s_deleted' % (module.__name__, base_name)
        status_view = '%s.views.%s_switch_status' % (module.__name__, base_name)
        logs_view = '%s.views.%s_logs' % (module.__name__, base_name)
        tag_search_view = '%s.views.%s_tag_search' % (module.__name__, base_name)
        mayi_view = '%s.views.%s_mayi' % (module.__name__, base_name)

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_blank=allow_blank, allow_all_units=allow_all_units)
        main_unit = None

        allow_all_units_ = allow_all_units  # Need a local copy

        if unit_mode:

            # Remove upk in urls (unit has been changed)
            if 'upk' in request.GET:
                get_params = dict(request.GET.iterlists())
                del get_params['upk']
                return HttpResponseRedirect('{}?{}'.format(request.path, urllib.urlencode(get_params)))

            from units.models import Unit

            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

            main_unit.set_rights_can_select(lambda unit: model_class.static_rights_can(right_to_check, request.user, unit, current_year))
            main_unit.set_rights_can_edit(lambda unit: model_class.static_rights_can(right_to_check_edit, request.user, unit, current_year))
            main_unit.check_if_can_use_hidden(request.user)

            allow_all_units_ = allow_all_units and model_class.static_rights_can(right_to_check, request.user, main_unit, current_year)
        else:
            # The LIST right is not verified here if we're in unit mode. We
            # need to test (in the view) in another unit is available for LIST
            # if the current unit isn't !
            if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can(right_to_check, request.user, current_unit, current_year):
                raise Http404

        if hasattr(model_class, 'moderable_object') and model_class.moderable_object:  # If the object is moderable, list all moderable things by the current user
            # List all moderiables in the 'todo' satate
            moderables = model_class.objects.filter(status=model_class.moderable_state).exclude(deleted=True)

            # Filter to check if user has rights
            moderables = filter(lambda m: m.rights_can('VALIDATE', request.user), moderables)
        else:
            moderables = False

        if object_filter and hasattr(model_class, 'get_linked_object_class'):
            objects = model_class.get_linked_object_class().objects.filter(unit=current_unit)
        else:
            objects = []

        if bonus_args_transformator:
            extra_data = bonus_args_transformator(request, **bonus_args) or {}
        else:
            extra_data = {}

        data = {
            'Model': model_class, 'json_view': json_view, 'edit_view': edit_view, 'deleted_view': deleted_view, 'show_view': show_view, 'status_view': status_view, 'logs_view': logs_view, 'tag_search_view': tag_search_view, 'mayi_view': mayi_view,
            'unit_mode': unit_mode, 'main_unit': main_unit, 'unit_blank': unit_blank, 'allow_all_units': allow_all_units_,
            'year_mode': year_mode, 'years_available': AccountingYear.build_year_menu('LIST', request.user),
            'moderables': moderables, 'object_filter': objects, 'tag_mode': tag_class is not None, 'tag': request.GET.get('tag', ''),
        }

        data.update(extra_data)

        if hasattr(model_class.MetaData, 'extra_args_for_list'):
            data.update(model_class.MetaData.extra_args_for_list(request, current_unit, current_year))

        return render(request, ['%s/%s/%s.html' % (module.__name__, base_name, template_to_use,), 'generic/generic/%s.html' % (template_to_use,)], data)

    return _generic_generic_list


def generate_list(module, base_name, model_class, tag_class):

    return generate_generic_list(module, base_name, model_class, '_list_json', 'LIST', 'CREATE', 'list', True, tag_class=tag_class, allow_all_units=True)


def generate_list_json(module, base_name, model_class, tag_class):

    @login_required
    @csrf_exempt
    def _generic_list_json(request):
        edit_view = '%s.views.%s_edit' % (module.__name__, base_name)
        show_view = '%s.views.%s_show' % (module.__name__, base_name)
        delete_view = '%s.views.%s_delete' % (module.__name__, base_name)
        logs_view = '%s.views.%s_logs' % (module.__name__, base_name)

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_all_units=True)

        if unit_mode:
            from units.models import Unit
            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

        all_units_mode = unit_mode and current_unit and current_unit.pk == -2

        if all_units_mode:
            unit_to_check = main_unit
        else:
            unit_to_check = current_unit

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('LIST', request.user, unit_to_check, current_year):
            raise Http404

        if unit_mode and not all_units_mode:

            if not current_unit:
                if request.user.is_superuser or model_class.static_rights_can('LIST', request.user, main_unit, current_year):  # Never filter
                    filter_ = lambda x: x.filter(unit=None)
                else:
                    filter_ = lambda x: x.filter(unit=None, unit_blank_user=request.user)
            else:
                if hasattr(model_class.MetaData, 'costcenterlinked') and model_class.MetaData.costcenterlinked:
                    filter_ = lambda x: x.filter(Q(costcenter__deleted=False) & (Q(costcenter__unit=current_unit) | (Q(costcenter__unit__parent_hierarchique=current_unit) & Q(costcenter__unit__is_commission=False))))
                else:
                    filter_ = lambda x: x.filter(unit=current_unit)
        else:
            filter_ = lambda x: x

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        if hasattr(model_class.MetaData, 'extra_filter_for_list'):
            filter___ = model_class.MetaData.extra_filter_for_list(request, unit_to_check, current_year, filter__)
        else:
            filter___ = filter__

        tag = request.GET.get('tag')

        if tag_class and tag:
            filter____ = lambda x: filter___(x).filter(tags__tag=tag).distinct()
        else:
            filter____ = filter___

        return generic_list_json(request, model_class, [col for (col, disp) in model_class.MetaData.list_display] + ['pk'], [module.__name__ + '/' + base_name + '/list_json.html', 'generic/generic/list_json.html'],
            {'Model': model_class,
             'show_view': show_view,
             'edit_view': edit_view,
             'delete_view': delete_view,
             'logs_view': logs_view,
             'list_display': model_class.MetaData.list_display,
             'all_units_mode': all_units_mode,
            },
            True, model_class.MetaData.filter_fields,
            bonus_filter_function=filter____,
            selector_column=True,
            bonus_total_filter_function=filter___,
        )

    return _generic_list_json


def generate_list_related(module, base_name, model_class):

    return generate_generic_list(module, base_name, model_class, '_list_related_json', 'VALIDATE', 'VALIDATE', 'list_related', False, True)


def generate_list_related_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generate_list_related_json(request):

        edit_view = '%s.views.%s_edit' % (module.__name__, base_name)
        show_view = '%s.views.%s_show' % (module.__name__, base_name)
        delete_view = '%s.views.%s_delete' % (module.__name__, base_name)
        logs_view = '%s.views.%s_logs' % (module.__name__, base_name)

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_blank=False)

        if unit_mode:
            if hasattr(model_class.MetaState, 'filter_unit_field'):
                filter_ = lambda x: x.filter(**{model_class.MetaState.filter_unit_field.replace('.', '__'): current_unit}).distinct()
            else:
                filter_ = lambda x: x.filter(**{model_class.MetaState.unit_field.replace('.', '__'): current_unit}).distinct()
        else:
            filter_ = lambda x: x.distinct()

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        def filter_object(qs, request):
            if request.POST.get('sSearch_0'):
                if hasattr(model_class.MetaState, 'filter_unit_field'):
                    return qs.filter(**{'__'.join(model_class.MetaState.filter_unit_field.split('.')[:-1] + ['pk']): request.POST.get('sSearch_0'), model_class.MetaState.filter_unit_field.replace('.', '__'): current_unit})
                else:
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

    return _generate_list_related_json


def generate_edit(module, base_name, model_class, form_class, log_class, file_class, tag_class):
    from accounting_tools.models import LinkedInfo

    @login_required
    def _generic_edit(request, pk):

        list_view = '%s.views.%s_list' % (module.__name__, base_name)
        list_related_view = '%s.views.%s_list_related' % (module.__name__, base_name)
        show_view = '%s.views.%s_show' % (module.__name__, base_name)
        file_upload_view = '%s.views.%s_file_upload' % (module.__name__, base_name)
        file_delete_view = '%s.views.%s_file_delete' % (module.__name__, base_name)
        file_get_view = '%s.views.%s_file_get' % (module.__name__, base_name)
        file_get_thumbnail_view = '%s.views.%s_file_get_thumbnail' % (module.__name__, base_name)
        tag_search_view = '%s.views.%s_tag_search' % (module.__name__, base_name)

        related_mode = request.GET.get('_fromrelated') == '_'

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        extra_args = {}

        try:
            obj = model_class.objects.get(pk=pk, deleted=False)

            if unit_mode:

                obj_unit = obj.costcenter.unit if isinstance(obj, CostCenterLinked) else obj.unit

                update_current_unit(request, obj_unit.pk if obj_unit else -1)
                current_unit = obj_unit

            if year_mode:
                update_current_year(request, obj.accounting_year.pk)
                current_year = obj.accounting_year

            if isinstance(obj, BasicRightModel) and not obj.rights_can('EDIT', request.user):
                raise Http404

        except (ValueError, model_class.DoesNotExist):
            obj = model_class()

            if hasattr(model_class, 'MetaEdit') and hasattr(model_class.MetaEdit, 'set_extra_defaults'):
                model_class.MetaEdit.set_extra_defaults(obj, request)

            if unit_mode:
                if unit_blank and not current_unit:
                    obj.unit_blank_user = request.user

                if has_property(obj, 'MetaData.costcenterlinked') and obj.MetaData.costcenterlinked and current_unit.costcenter_set.first():
                    obj.costcenter = current_unit.costcenter_set.first()

                if has_property(obj, obj.MetaRights.linked_unit_property):
                    set_property(obj, obj.MetaRights.linked_unit_property, current_unit)
                else:
                    obj.unit = current_unit

            if year_mode:

                # Est-ce qu'on va tenter de créer un truc dans une année
                # comptable pas possible ?
                if current_year not in AccountingYear.build_year_menu('CREATE', request.user):
                    update_current_year(request, None)
                    ___, current_year, ___ = get_year_data(model_class, request)

                obj.accounting_year = current_year

            if unit_mode and isinstance(obj, BasicRightModel) and not obj.rights_can('CREATE', request.user) and current_unit:
                # Try to find a suitable unit, since the user may access
                # this page without using a create button (who switched the
                # unit)
                from units.models import Unit
                for test_unit in Unit.objects.order_by('?'):

                    if has_property(obj, obj.MetaRights.linked_unit_property):
                        set_property(obj, obj.MetaRights.linked_unit_property, test_unit)
                    else:
                        obj.unit = test_unit

                    if obj.rights_can('CREATE', request.user):
                        current_unit = test_unit
                        break

                # Set the original (or new) unit
                if has_property(obj, obj.MetaRights.linked_unit_property):
                    set_property(obj, obj.MetaRights.linked_unit_property, current_unit)
                else:
                    obj.unit = current_unit

            if isinstance(obj, BasicRightModel) and not obj.rights_can('CREATE', request.user):
                raise Http404

        if unit_mode:
            from units.models import Unit

            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

            main_unit.set_rights_can_select(lambda unit: model_class.static_rights_can('CREATE', request.user, unit, current_year))
            main_unit.set_rights_can_edit(lambda unit: model_class.static_rights_can('CREATE', request.user, unit, current_year))
            main_unit.check_if_can_use_hidden(request.user)
        else:
            main_unit = None

        if obj.pk:
            before_data = obj.build_state()
        else:
            before_data = None

        file_mode = file_class is not None
        file_key = None  # Will be set later

        from generic.models import GenericModelWithLines

        lines_objects = []

        if issubclass(model_class, GenericModelWithLines):

            lines_objects = filter(lambda lo: not hasattr(obj.MetaEdit, 'only_if') or lo['related_name'] not in obj.MetaEdit.only_if or obj.MetaEdit.only_if[lo['related_name']]((obj, request.user)), copy.deepcopy(obj.MetaLines.lines_objects))

            for line_data in lines_objects:
                line_data['form'] = getattr(importlib.import_module('.'.join(line_data['form'].split('.')[:-1])), line_data['form'].split('.')[-1])
                line_data['class'] = getattr(importlib.import_module('.'.join(line_data['class'].split('.')[:-1])), line_data['class'].split('.')[-1])

                line_data['new_form'] = line_data['form'](prefix="_LINES_%s_-ID-" % (line_data['related_name'],))
                line_data['forms'] = []

        tag_mode = tag_class is not None
        tags = []

        if tag_mode:
            tags_before = ','.join([t.tag for t in obj.tags.order_by('tag')]) if obj.pk else ''

        linked_info_mode = hasattr(model_class, 'MetaEdit') and hasattr(model_class.MetaEdit, 'set_linked_info') and model_class.MetaEdit.set_linked_info

        if request.method == 'POST':  # If the form has been submitted...
            form = form_class(request.user, request.POST, request.FILES, instance=obj)

            form.truffe_request = request

            if file_mode:
                file_key = request.POST.get('file_key')

            if tag_mode:
                tags = filter(lambda t: t, request.POST.get('tags').split(','))

            all_forms_valids = True

            for line_data in lines_objects:

                for submited_id in request.POST.getlist('_LINES_LIST_%s[]' % (line_data['related_name'], )):
                    if submited_id != '-ID-':

                        if submited_id.startswith('NEW-'):
                            line_instance = line_data['class'](**{line_data['field']: obj})
                        else:
                            line_instance = get_object_or_404(line_data['class'], pk=submited_id, **{line_data['field']: obj})

                        line_old_val = line_instance.__unicode__()

                        line_form = line_data['form'](request.POST, request.FILES, instance=line_instance, prefix="_LINES_%s_%s" % (line_data['related_name'], submited_id))

                        if not line_form.is_valid():
                            all_forms_valids = False

                        line_form_data = {'id': submited_id, 'form': line_form, 'old_val': line_old_val}

                        line_data['forms'].append(line_form_data)

            form._clean_line_data = lines_objects

            if form.is_valid() and all_forms_valids:  # If the form is valid

                right = 'EDIT' if obj.pk else 'CREATE'
                obj = form.save(commit=False)
                if not obj.rights_can(right, request.user):
                    messages.error(request, _(u'Tu n\'as pas le droit de créer/modifier cet objet.'))
                    return redirect('{}.views.{}_edit'.format(module.__name__, base_name), pk='~' if right == 'CREATE' else obj.pk)

                obj.save()
                if hasattr(form, 'save_m2m'):
                    form.save_m2m()

                lines_adds = {}
                lines_updates = {}
                lines_deletes = {}

                for line_data in lines_objects:
                    valids_ids = []

                    line_order = 0

                    for line_form in line_data['forms']:
                        line_obj = line_form['form'].save(commit=False)
                        setattr(line_obj, line_data['field'], obj)

                        if not line_obj.pk:
                            lines_adds['%s' % (line_data['related_name'],)] = line_obj.__unicode__()
                        else:
                            if line_form['old_val'] != line_obj.__unicode__():
                                lines_updates['%s #%s' % (line_data['related_name'], line_obj.pk,)] = (line_form['old_val'], line_obj.__unicode__())

                        if line_data['sortable']:
                            line_obj.order = line_order
                            line_order += 1

                        line_obj.save()

                        valids_ids.append(line_obj.pk)

                    for line_deleted in getattr(obj, line_data['related_name']).exclude(pk__in=valids_ids):

                        lines_deletes['%s #%s' % (line_data['related_name'], line_deleted.pk,)] = line_deleted.__unicode__()

                        line_deleted.delete()

                if file_mode:
                    files_data = request.session.get('pca_files_%s' % (file_key,))

                    if files_data is None:
                        messages.warning(request, _(u'Erreur lors de la récupération de la session pour la gestion des fichiers. Il est possible que le formulaire aie été sauvegardé deux fois. Vérifiez si l\'état actuel des fichiers correspond à ce que vous désirez !'))
                    else:

                        for file_pk in files_data:
                            file_obj = file_class.objects.get(pk=file_pk)

                            if file_obj.object != obj:
                                file_obj.object = obj
                                file_obj.save()
                                log_class(who=request.user, what='file_added', object=obj, extra_data=file_obj.basename()).save()

                        for file_obj in obj.files.all():
                            if file_obj.pk not in files_data:
                                log_class(who=request.user, what='file_removed', object=obj, extra_data=file_obj.basename()).save()
                                os.unlink(file_obj.file.path)
                                file_obj.delete()

                        # Clean up session
                        del request.session['pca_files_%s' % (file_key,)]

                if tag_mode:
                    for t in tags:
                        __, ___ = tag_class.objects.get_or_create(tag=t, object=obj)

                    tag_class.objects.filter(object=obj).exclude(tag__in=tags).delete()

                    tags_after = ', '.join([t.tag for t in obj.tags.order_by('tag')])

                if linked_info_mode:
                    object_ct = ContentType.objects.get(app_label=module.__name__, model=base_name)
                    infos, __ = LinkedInfo.objects.get_or_create(content_type=object_ct, object_id=obj.pk, defaults={'user_pk': obj.user.pk})
                    for (info_field, user_field) in (('first_name', 'first_name'), ('last_name', 'last_name'), ('address', 'adresse'), ('phone', 'mobile'), ('bank', 'nom_banque'), ('iban_ccp', 'iban_ou_ccp'), ('user_pk', 'pk')):
                        setattr(infos, info_field, getattr(obj.user, user_field))
                    infos.save()

                if isinstance(obj, BasicRightModel):
                    obj.rights_expire()

                if hasattr(obj, 'save_signal'):
                    obj.save_signal()

                if hasattr(obj, 'MetaEdit') and hasattr(obj.MetaEdit, 'do_extra_post_actions'):
                    extra_args = obj.MetaEdit.do_extra_post_actions(obj, request, request.POST, True)
                    for (lines, logs) in [(lines_adds, 'log_add'), (lines_updates, 'log_update'), (lines_deletes, 'log_delete')]:
                        lines.update(extra_args[logs])

                messages.success(request, _(u'Élément sauvegardé !'))

                if not before_data:
                    log_class(who=request.user, what='created', object=obj).save()

                    if hasattr(obj, 'create_signal'):
                        obj.create_signal(request)
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

                    added.update(lines_adds)
                    edited.update(lines_updates)
                    deleted.update(lines_deletes)

                    if tag_mode and tags_before != tags_after:
                        edited['tags'] = (tags_before, tags_after)

                    diff = {'added': added, 'edited': edited, 'deleted': deleted}

                    log_class(who=request.user, what='edited', object=obj, extra_data=json.dumps(diff)).save()

                obj.user_has_seen_object(request.user)

                if request.POST.get('post-save-dest'):
                    if request.POST.get('post-save-dest') == 'new':
                        return redirect(module.__name__ + '.views.' + base_name + '_edit', pk='~')
                    else:
                        return redirect(module.__name__ + '.views.' + base_name + '_edit', pk=obj.pk)

                return HttpResponseRedirect('%s%s' % (reverse(module.__name__ + '.views.' + base_name + '_show', args=(obj.pk,)), '?_upkns=_&_fromrelated=_' if related_mode else ''))
            else:
                if hasattr(obj, 'MetaEdit') and hasattr(obj.MetaEdit, 'do_extra_post_actions'):
                    extra_args = obj.MetaEdit.do_extra_post_actions(obj, request, request.POST, False)

        else:
            form = form_class(request.user, instance=obj)

            if file_mode:

                # Generate a new file session
                file_key = str(uuid.uuid4())
                request.session['pca_files_%s' % (file_key,)] = [f.pk for f in obj.files.all()] if obj.pk else []

            # Init subforms
            for line_data in lines_objects:
                if obj.pk:
                    line_objs = getattr(obj, line_data['related_name'])

                    if line_data['sortable']:
                        line_objs = line_objs.order_by('order')
                    else:
                        line_objs = line_objs.order_by('pk')

                    for line_obj in line_objs:
                        line_form = line_data['form'](instance=line_obj, prefix="_LINES_%s_%s" % (line_data['related_name'], line_obj.pk))
                        line_form_data = {'id': line_obj.pk, 'form': line_form}
                        line_data['forms'].append(line_form_data)

            if tag_mode:
                tags = [t.tag for t in obj.tags.all()] if obj.pk else []

        if file_mode:
            if 'pca_files_%s' % (file_key,) in request.session:
                files = [file_class.objects.get(pk=pk_) for pk_ in request.session['pca_files_%s' % (file_key,)]]
            else:
                files = None
                messages.warning(request, _(u'Erreur lors de la récupération de la session pour la gestion des fichiers. Il est possible que le formulaire aie été sauvegardé deux fois. Vérifiez si l\'état actuel des fichiers correspond à ce que vous désirez !'))

        else:
            files = None

        costcenter_mode = isinstance(obj, CostCenterLinked)

        data = {'Model': model_class, 'form': form, 'list_view': list_view, 'show_view': show_view, 'unit_mode': unit_mode, 'current_unit': current_unit,
                'main_unit': main_unit, 'unit_blank': unit_blank, 'year_mode': year_mode, 'current_year': current_year,
                'years_available': AccountingYear.build_year_menu('EDIT' if obj.pk else 'CREATE', request.user), 'related_mode': related_mode, 'list_related_view': list_related_view,
                'file_mode': file_mode, 'file_upload_view': file_upload_view, 'file_delete_view': file_delete_view, 'files': files, 'file_key': file_key, 'file_get_view': file_get_view,
                'file_get_thumbnail_view': file_get_thumbnail_view, 'lines_objects': lines_objects, 'costcenter_mode': costcenter_mode, 'tag_mode': tag_mode, 'tags': tags,
                'tag_search_view': tag_search_view, 'extra_args': extra_args.get('display', '')}

        if hasattr(model_class.MetaData, 'extra_args_for_edit'):
            data.update(model_class.MetaData.extra_args_for_edit(request, current_unit, current_year))

        return render(request, ['%s/%s/edit.html' % (module.__name__, base_name), 'generic/generic/edit.html'], data)

    return _generic_edit


def generate_show(module, base_name, model_class, log_class, tag_class):

    @login_required
    def _generic_show(request, pk):

        edit_view = '%s.views.%s_edit' % (module.__name__, base_name)
        delete_view = '%s.views.%s_delete' % (module.__name__, base_name)
        log_view = '%s.views.%s_log' % (module.__name__, base_name)
        list_view = '%s.views.%s_list' % (module.__name__, base_name)
        list_related_view = '%s.views.%s_list_related' % (module.__name__, base_name)
        status_view = '%s.views.%s_switch_status' % (module.__name__, base_name)
        contact_view = '%s.views.%s_contact' % (module.__name__, base_name)
        file_get_view = '%s.views.%s_file_get' % (module.__name__, base_name)
        file_get_thumbnail_view = '%s.views.%s_file_get_thumbnail' % (module.__name__, base_name)

        related_mode = request.GET.get('_fromrelated') == '_'

        obj = get_object_or_404(model_class, pk=pk)

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        if unit_mode:
            unit = obj.costcenter.unit if isinstance(obj, CostCenterLinked) else obj.unit
            update_current_unit(request, unit.pk if unit else -1)
            current_unit = unit

        if year_mode:
            update_current_year(request, obj.accounting_year.pk)
            current_year = obj.accounting_year

        if isinstance(obj, BasicRightModel) and not obj.rights_can('SHOW', request.user):
            raise Http404

        if obj.deleted:
            return render(request, ['%s/%s/show_deleted.html' % (module.__name__, base_name), 'generic/generic/show_deleted.html'], {
                'Model': model_class, 'delete_view': delete_view, 'edit_view': edit_view, 'log_view': log_view, 'list_view': list_view, 'status_view': status_view, 'contact_view': contact_view, 'list_related_view': list_related_view, 'file_get_view': file_get_view, 'file_get_thumbnail_view': file_get_thumbnail_view,
                'obj': obj,
            })

        rights = []

        if hasattr(model_class, 'MetaRights'):

            for key, info in obj.MetaRights.rights.iteritems():
                rights.append((key, info, obj.rights_can(key, request.user)))

        log_entires = log_class.objects.filter(object=obj).order_by('-when').all()

        if hasattr(obj, 'contactables_groups'):
            contactables_groups = obj.contactables_groups()
        else:
            contactables_groups = None

        lines_objects = []

        from generic.models import GenericModelWithLines

        if issubclass(model_class, GenericModelWithLines):

            lines_objects = copy.deepcopy(obj.MetaLines.lines_objects)

            for line_data in lines_objects:

                line_objs = getattr(obj, line_data['related_name'])

                if line_data['sortable']:
                    line_objs = line_objs.order_by('order')
                else:
                    line_objs = line_objs.order_by('pk')

                line_data['elems'] = line_objs

        tags = []

        if tag_class:
            tags = [t.tag for t in obj.tags.order_by('tag')]

        obj.user_has_seen_object(request.user)

        return render(request, ['%s/%s/show.html' % (module.__name__, base_name), 'generic/generic/show.html'], {
            'Model': model_class, 'delete_view': delete_view, 'edit_view': edit_view, 'log_view': log_view, 'list_view': list_view, 'status_view': status_view, 'contact_view': contact_view, 'list_related_view': list_related_view, 'file_get_view': file_get_view, 'file_get_thumbnail_view': file_get_thumbnail_view,
            'obj': obj, 'log_entires': log_entires,
            'rights': rights,
            'unit_mode': unit_mode, 'current_unit': current_unit,
            'year_mode': year_mode, 'current_year': current_year,
            'contactables_groups': contactables_groups,
            'related_mode': related_mode, 'lines_objects': lines_objects,
            'tags': tags,
        })

    return _generic_show


def generate_delete(module, base_name, model_class, log_class):

    @login_required
    def _generic_delete(request, pk):

        list_view = '%s.views.%s_list' % (module.__name__, base_name)
        list_related_view = '%s.views.%s_list_related' % (module.__name__, base_name)
        show_view = '%s.views.%s_show' % (module.__name__, base_name)

        related_mode = request.GET.get('_fromrelated') == '_'

        objs = [get_object_or_404(model_class, pk=pk_, deleted=False) for pk_ in filter(lambda x: x, pk.split(','))]

        multi_obj = len(objs) > 1

        for obj in objs:
            unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)
            year_mode, current_year, AccountingYear = get_year_data(model_class, request)
            if unit_mode:
                if isinstance(obj, CostCenterLinked):
                    update_current_unit(request, obj.costcenter.unit.pk if obj.costcenter.unit else -1)
                else:
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
                    obj.delete_signal(request)
                obj.save()

                log_class(who=request.user, what='deleted', object=obj).save()

                messages.success(request, _(u'Élément supprimé !'))

            if related_mode:
                return redirect(list_related_view)
            else:
                return redirect(list_view)

        return render(request, ['%s/%s/delete.html' % (module.__name__, base_name), 'generic/generic/delete.html'], {
            'Model': model_class, 'show_view': show_view, 'list_view': list_view, 'list_related_view': list_related_view,
            'objs': objs, 'can_delete': can_delete, 'can_delete_message': can_delete_message,
            'related_mode': related_mode, 'multi_obj': multi_obj, 'prob_obj': prob_obj
        })

    return _generic_delete


def generate_deleted(module, base_name, model_class, log_class):

    @login_required
    def _generic_deleted(request):

        list_view = '%s.views.%s_list' % (module.__name__, base_name)

        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('RESTORE', request.user, current_unit, current_year):
            raise Http404

        if unit_mode:
            from units.models import Unit

            main_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)

            main_unit.set_rights_can_select(lambda unit: model_class.static_rights_can('RESTORE', request.user, unit, current_year))
            main_unit.set_rights_can_edit(lambda unit: model_class.static_rights_can('RESTORE', request.user, unit, current_year))
            main_unit.check_if_can_use_hidden(request.user)
        else:
            main_unit = None

        if request.method == 'POST':
            obj = get_object_or_404(model_class, pk=request.POST.get('pk'), deleted=True)

            if unit_mode:
                if isinstance(obj, CostCenterLinked):
                    update_current_unit(request, obj.costcenter.unit.pk if obj.costcenter.unit else -1)
                else:
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
            if isinstance(model_class(), CostCenterLinked):
                liste = liste.filter(costcenter__unit=current_unit)
            else:
                liste = liste.filter(unit=current_unit)

        if year_mode:
            liste = liste.filter(accounting_year=current_year)
        else:
            liste = liste.all()

        return render(request, ['%s/%s/deleted.html' % (module.__name__, base_name), 'generic/generic/deleted.html'], {
            'Model': model_class, 'list_view': list_view, 'liste': liste,
            'unit_mode': unit_mode, 'current_unit': current_unit, 'main_unit': main_unit, 'unit_blank': unit_blank,
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

        list_view = '%s.views.%s_list' % (module.__name__, base_name)
        status_view = '%s.views.%s_switch_status' % (module.__name__, base_name)

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
            bonus_form = model_class.MetaState.states_bonus_form.get((obj.status, dest_status), model_class.MetaState.states_bonus_form.get(dest_status, None))

            if bonus_form and hasattr(bonus_form, '__call__') and not inspect.isclass(bonus_form):
                bonus_form = bonus_form(request, obj)

        if can_switch and request.method == 'POST' and request.POST.get('do') == 'it':

            for obj in objs:
                old_status = obj.status
                obj.status = dest_status
                obj.user_has_seen_object(request.user)
                obj.save()

                if isinstance(obj, BasicRightModel):
                    obj.rights_expire()

                if hasattr(obj, 'switch_status_signal'):
                    obj.switch_status_signal(request, old_status, dest_status)

                log_class(who=request.user, what='state_changed', object=obj, extra_data=json.dumps({'old': unicode(obj.MetaState.states.get(old_status)), 'new': unicode(obj.MetaState.states.get(dest_status)), 'old_code': old_status})).save()

                storage = messages.get_messages(request)
                if not storage:
                    messages.success(request, _(u'Statut modifié !'))
                storage.used = False
                done = True
                no_more_access = not obj.rights_can('SHOW', request.user)

                if no_more_access:
                    messages.warning(request, _(u'Vous avez perdu le droit de voir l\'objet !'))

                obj.user_has_seen_object(request.user)

        return render(request, ['%s/%s/switch_status.html' % (module.__name__, base_name), 'generic/generic/switch_status.html'], {
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

        contact_view = '%s.views.%s_contact' % (module.__name__, base_name)
        show_view = '%s.views.%s_show' % (module.__name__, base_name)

        obj = get_object_or_404(model_class, pk=pk, deleted=False)

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)
        year_mode, current_year, AccountingYear = get_year_data(model_class, request)

        if unit_mode:
            if isinstance(obj, CostCenterLinked):
                update_current_unit(request, obj.costcenter.unit.pk if obj.costcenter.unit else -1)
            else:
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

                if form.cleaned_data['receive_copy']:
                    send_templated_mail(request, _('Truffe :: Contact :: %s') % (form.cleaned_data['subject'],), request.user.email, [request.user.email], 'generic/generic/mail/contact', context)

                done = True
                messages.success(request, _(u'Message envoyé !'))
        else:
            form = ContactForm(contactables_groups, initial={'key': key})

        return render(request, ['%s/%s/contact.html' % (module.__name__, base_name), 'generic/generic/contact.html'], {
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

        liste = filter__(model_class.objects.exclude((Q(start_date__lt=start) & Q(end_date__lt=start)) | (Q(start_date__gt=end) & Q(end_date__gt=end))).filter(Q(status='1_asking') | Q(status='2_online')))

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

            if hasattr(l, 'get_linked_object'):
                linked_object = l.get_linked_object()

                if isinstance(linked_object, list):
                    titre = u'{} (Géré par {})'.format(u', '.join([o.__unicode__() for o in linked_object]), linked_object[0].unit)
                else:
                    titre = u'{} (Géré par {})'.format(l.get_linked_object(), l.get_linked_object().unit)
            else:
                titre = u'{}'.format(l)

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

        if unit_mode and model_class.MetaState.unit_field != '!root':
            if hasattr(model_class.MetaState, 'filter_unit_field'):
                filter_ = lambda x: x.filter(**{model_class.MetaState.filter_unit_field.replace('.', '__'): current_unit})
            else:
                filter_ = lambda x: x.filter(**{model_class.MetaState.unit_field.replace('.', '__'): current_unit})

        else:
            filter_ = lambda x: x

        if year_mode:
            filter__ = lambda x: filter_(x).filter(accounting_year=current_year)
        else:
            filter__ = filter_

        if request.GET.get('filter_object'):
            if hasattr(model_class.MetaState, 'filter_unit_field'):
                filter___ = lambda x: x.filter(**{'__'.join(model_class.MetaState.filter_unit_field.split('.')[:-1] + ['pk']): request.GET.get('filter_object'), model_class.MetaState.filter_unit_field.replace('.', '__'): current_unit})
            else:
                filter___ = lambda x: x.filter(**{'__'.join(model_class.MetaState.unit_field.split('.')[:-1] + ['pk']): request.GET.get('filter_object'), model_class.MetaState.unit_field.replace('.', '__'): current_unit})
        else:
            filter___ = lambda x: x

        if hasattr(model_class, 'static_rights_can') and not model_class.static_rights_can('VALIDATE', request.user, current_unit, current_year):
            raise Http404

        start = request.GET.get('start')

        end = request.GET.get('end')

        start = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(start)))
        end = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(end)))

        liste = filter___(filter__(model_class.objects.exclude((Q(start_date__lt=start) & Q(end_date__lt=start)) | (Q(start_date__gt=end) & Q(end_date__gt=end))).filter(Q(status='1_asking') | Q(status='2_online')))).exclude(deleted=True).distinct()

        retour = []

        colors = ['default', 'danger', 'success', 'warning', 'info', 'primary']

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

            if hasattr(l, 'get_linked_object'):
                lobj = l.get_linked_object()
                if isinstance(lobj, list):
                    titre = u'{} (Réservé par {})'.format(u', '.join([o.__unicode__() for o in lobj]), par)
                    colored = colors[lobj[0].pk % len(colors)]
                else:
                    titre = u'{} (Réservé par {})'.format(lobj, par)
                    colored = colors[lobj.pk % len(colors)]
            else:
                titre = u'{} (Réservé par {})'.format(l, par)
                colored = ""

            retour.append({'title': titre, 'start': str(l.start_date), 'end': str(l.end_date), 'className': className, 'icon': icon, 'url': url, 'allDay': False, 'description': str(l), 'colored': colored})

        return HttpResponse(json.dumps(retour))

    return _generic_calendar_related_json


def generate_calendar_specific(module, base_name, model_class):

    def _check_and_add_context(request, pk):
        base_model = model_class.get_linked_object_class()

        cobject = get_object_or_404(base_model, pk=pk, deleted=False, allow_calendar=True)

        if not cobject.allow_externals and request.user.is_external():
            raise Http404()

        if not cobject.allow_external_calendar and request.user.is_external():
            raise Http404()

        return {'cobject': cobject}

    return generate_generic_list(module, base_name, model_class, '_calendar_specific_json', 'SHOW', 'SHOW', 'calendar_specific', False, bonus_args_transformator=_check_and_add_context)


def generate_calendar_specific_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generic_calendar_specific_json(request, pk):

        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request, allow_blank=False)

        base_model = model_class.get_linked_object_class()

        cobject = get_object_or_404(base_model, pk=pk, deleted=False, allow_calendar=True)

        if not cobject.allow_externals and request.user.is_external():
            raise Http404()

        if not cobject.allow_external_calendar and request.user.is_external():
            raise Http404()

        filter_ = lambda x: x.filter(**{'__'.join(model_class.MetaState.unit_field.split('.')[:-1] + ['pk']): cobject.pk})

        start = request.GET.get('start')

        end = request.GET.get('end')

        start = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(start)))
        end = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(float(end)))

        liste = filter_(model_class.objects.exclude((Q(start_date__lt=start) & Q(end_date__lt=start)) | (Q(start_date__gt=end) & Q(end_date__gt=end))).filter(Q(status='1_asking') | Q(status='2_online'))).exclude(deleted=True)

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

            titre = par

            retour.append({'title': titre, 'start': str(l.start_date), 'end': str(l.end_date), 'className': className, 'icon': icon, 'url': url, 'allDay': False, 'description': str(l)})

        return HttpResponse(json.dumps(retour))

    return _generic_calendar_specific_json


def generate_directory(module, base_name, model_class):

    @login_required
    def _generic_directory(request):

        if not model_class.static_rights_can('CREATE', request.user):
            raise Http404

        from units.models import Unit

        edit_view = '%s.views.%s_edit' % (module.__name__, base_name)
        calendar_specific_view = '%s.views.%s_calendar_specific' % (module.__name__, base_name)

        units = model_class.get_linked_object_class().objects.order_by('unit__name').filter(deleted=False)

        if request.user.is_external():
            units = units.filter(allow_externals=True)

        units = [Unit.objects.get(pk=u['unit']) for u in units.values('unit').distinct()]

        for unit in units:
            unit.directory_objects = model_class.get_linked_object_class().objects.filter(unit=unit, deleted=False).order_by('title')

            if request.user.is_external():
                unit.directory_objects = unit.directory_objects.filter(allow_externals=True)

        return render(request, ['%s/%s/directory.html' % (module.__name__, base_name), 'generic/generic/directory.html'], {
            'Model': model_class, 'edit_view': edit_view, 'calendar_specific_view': calendar_specific_view,
            'units': units,
        })

    return _generic_directory


def generate_logs(module, base_name, model_class):

    @login_required
    def _generic_logs(request):

        # Le check des droits éventuelles est ultra complexe: il faut affichier
        # les logs seulement des objets sur les quels l'users à le droit
        # 'DISPLAY_LOG', hors c'est pas checkable via la base et il faut
        # paginer. Le faire manuellement serait horible au niveau performances
        # (par exemple en listant d'abord tous les objets puit en filtrant les
        # logs via la liste d'objects possibles).
        if not request.user.is_superuser:
            raise Http404

        logs_json_view = '%s.views.%s_logs_json' % (module.__name__, base_name)
        list_view = '%s.views.%s_list' % (module.__name__, base_name)

        data = {
            'Model': model_class, 'logs_json_view': logs_json_view, 'list_view': list_view,
        }

        return render(request, ['%s/%s/logs.html' % (module.__name__, base_name), 'generic/generic/logs.html'], data)

    return _generic_logs


def generate_logs_json(module, base_name, model_class, logging_class):

    @login_required
    @csrf_exempt
    def _generic_logs_json(request):

        if not request.user.is_superuser:
            raise Http404

        show_view = '%s.views.%s_show' % (module.__name__, base_name)
        list_view = '%s.views.%s_list' % (module.__name__, base_name)

        bonus_filter = []

        for potential_str in ['title', 'name']:
            if hasattr(model_class, potential_str):
                bonus_filter += [potential_str]

        return generic_list_json(request, logging_class, ['object', 'unit', 'when', 'who', 'what', 'pk'], [module.__name__ + '/' + base_name + '/logs_json.html', 'generic/generic/logs_json.html'],
            {'Model': model_class,
             'list_view': list_view,
             'show_view': show_view,
            },
            not_sortable_columns=['unit',],
            filter_fields=['when', 'who__first_name', 'what'] + bonus_filter,
        )

    return _generic_logs_json


def generate_file_upload(module, base_name, model_class, log_class, file_class):

    @login_required
    def _generic_file_upload(request):

        file_delete_view = '%s.views.%s_file_delete' % (module.__name__, base_name)
        file_get_view = '%s.views.%s_file_get' % (module.__name__, base_name)
        file_get_thumbnail_view = '%s.views.%s_file_get_thumbnail' % (module.__name__, base_name)

        key = request.GET.get('key')

        file = upload_receive(request)

        instance = file_class(file=file, uploader=request.user)
        instance.save()

        basename = os.path.basename(instance.file.path)

        file_dict = {
            'name': basename,
            'size': file.size,

            'url': reverse(file_get_view, kwargs={'pk': instance.pk}),
            'thumbnailUrl': reverse(file_get_thumbnail_view, kwargs={'pk': instance.pk}),
            'deleteUrl': '%s?key=%s' % (reverse(file_delete_view, kwargs={'pk': instance.pk}), key),
            'deleteType': 'POST',
        }

        # Can't do it in one line !
        try:
            file_list = request.session['pca_files_%s' % (key,)]
        except KeyError:
            return HttpResponseNotFound()

        file_list.append(instance.pk)
        request.session['pca_files_%s' % (key,)] = file_list

        return UploadResponse(request, file_dict)

    return _generic_file_upload


def generate_file_delete(module, base_name, model_class, log_class, file_class):

    @login_required
    def _generic_file_delete(request, pk):

        success = True

        key = request.GET.get('key')

        if int(pk) not in request.session['pca_files_%s' % (key,)]:
            raise Http404()

        try:
            instance = file_class.objects.get(pk=pk)

            if not instance.object:  # Deleted later if linked
                os.unlink(instance.file.path)
                instance.delete()

            file_list = request.session['pca_files_%s' % (key,)]
            file_list.remove(int(pk))
            request.session['pca_files_%s' % (key,)] = file_list

        except file_class.DoesNotExist:
            success = False

        return JFUResponse(request, success)
    return _generic_file_delete


def generate_file_get(module, base_name, model_class, log_class, file_class):

    @login_required
    def _generic_file_get(request, pk):

        instance = get_object_or_404(file_class, pk=pk)

        if not instance.object:  # Just uploaded
            if instance.uploader != request.user:
                raise Http404
        else:
            if isinstance(instance.object, BasicRightModel) and not instance.object.rights_can('SHOW', request.user):
                raise Http404

        return sendfile(request, instance.file.path, 'down' in request.GET)

    return _generic_file_get


def generate_file_get_thumbnail(module, base_name, model_class, log_class, file_class):

    @login_required
    def _generic_file_thumbnail(request, pk):

        instance = get_object_or_404(file_class, pk=pk)

        if not instance.object:  # Just uploaded
            if instance.uploader != request.user:
                raise Http404
        else:
            if isinstance(instance.object, BasicRightModel) and not instance.object.rights_can('SHOW', request.user):
                raise Http404

        remove_me = None

        if instance.is_picture():
            url = instance.file
        elif instance.is_pdf():
            try:

                url = os.path.join('cache', 'pdfthumbnail', "{}.jpg".format(instance.file.name.replace('/', '_')))
                full_url = os.path.join(settings.MEDIA_ROOT, url)

                if not os.path.isfile(full_url):
                    with Image(filename="{}{}[0]".format(settings.MEDIA_ROOT, instance.file)) as img:
                        img.save(filename=full_url)
            except:
                url = 'img/PDF.png'
        else:
            url = 'img/File.png'

        options = {'size': (int(request.GET.get('w', 200)), int(request.GET.get('h', 100))), 'crop': True, 'upscale': True}
        thumb = get_thumbnailer(url).get_thumbnail(options)

        if remove_me:
            os.unlink(remove_me)

        return sendfile(request, '%s%s' % (settings.MEDIA_ROOT, thumb,))

    return _generic_file_thumbnail


def generate_tag_search(module, base_name, model_class, log_class, tag_class):

    @login_required
    def _generic_tag_search(request):

        upk = request.GET.get('upk')

        if upk:
            from units.models import Unit
            unit = get_object_or_404(Unit, pk=upk)
        else:
            unit = None

        ypk = request.GET.get('ypk')

        if ypk:
            from accounting_core.models import AccountingYear
            year = get_object_or_404(AccountingYear, pk=ypk)
        else:
            year = None

        q = request.GET.get('q')

        tags = tag_class.objects

        if q:
            tags = tags.filter(tag__istartswith=q)

        if unit:
            if isinstance(model_class(), CostCenterLinked):
                tags = tags.filter(object__costcenter__unit=unit)
            else:
                tags = tags.filter(object__unit=unit)

        if year:
            tags = tags.filter(object__accounting_year=year)

        retour = []

        for t in tags.order_by('tag'):
            if t.tag not in retour:
                retour.append(t.tag)

        retour = [{'id': tag, 'text': tag} for tag in retour]

        return HttpResponse(json.dumps(retour), content_type='text/json')

    return _generic_tag_search


def generate_mayi(module, base_name, model_class, logging_class):

    @login_required
    @csrf_exempt
    def _generic_mayi(request):
        year_mode, current_year, AccountingYear = get_year_data(model_class, request)
        unit_mode, current_unit, unit_blank = get_unit_data(model_class, request)

        retour = {}

        for r in ['RESTORE', 'CREATE']:
            retour[r] = model_class.static_rights_can(r, request.user, current_unit, current_year)

        return HttpResponse(json.dumps(retour), content_type='text/json')

    return _generic_mayi
