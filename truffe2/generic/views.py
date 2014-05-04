# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response, redirect
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


def generate_list(module, base_name, model_class):

    @login_required
    def _generic_list(request):

        json_view = module.__name__ + '.views.' + base_name + '_list_json'
        edit_view = module.__name__ + '.views.' + base_name + '_edit'

        return render_to_response([module.__name__ + '/' + base_name + '/list.html', 'generic/generic/list.html'], {
            'Model': model_class, 'json_view': json_view, 'edit_view': edit_view,
        }, context_instance=RequestContext(request))

    return _generic_list


def generate_list_json(module, base_name, model_class):

    @login_required
    @csrf_exempt
    def _generic_list_json(request):
        show_view = module.__name__ + '.views.' + base_name + '_show'
        edit_view = module.__name__ + '.views.' + base_name + '_edit'
        delete_view = module.__name__ + '.views.' + base_name + '_delete'
        logs_view = module.__name__ + '.views.' + base_name + '_logs'

        return generic_list_json(request, model_class, [col for (col, disp) in model_class.MetaData.list_display] + ['pk'], [module.__name__ + '/' + base_name + '/list_json.html', 'generic/generic/list_json.html'],
            {'Model': model_class,
             'show_view': show_view,
             'edit_view': edit_view,
             'delete_view': delete_view,
             'logs_view': logs_view},
            True
        )

    return _generic_list_json


def generate_edit(module, base_name, model_class, form_class):

    @login_required
    @csrf_exempt
    def _generic_edit(request, pk):
        list_view = module.__name__ + '.views.' + base_name + '_list'
        show_view = module.__name__ + '.views.' + base_name + '_show'

        try:
            obj = model_class.objects.get(pk=pk, deleted=False)
        except (ValueError, model_class.DoesNotExist):
            obj = model_class()

        if request.method == 'POST':  # If the form has been submitted...
            form = form_class(request.user, request.POST, instance=obj)

            if form.is_valid():  # If the form is valid
                obj = form.save()

                messages.success(request, _(u'Élément sauvegardé !'))

                return redirect(module.__name__ + '.views.' + base_name + '_show', pk=obj.pk)
        else:
            form = form_class(request.user, instance=obj)

        return render_to_response([module.__name__ + '/' + base_name + '/edit.html', 'generic/generic/edit.html'], {'Model': model_class, 'form': form, 'list_view': list_view, 'show_view': show_view}, context_instance=RequestContext(request))

    return _generic_edit


def generate_show(module, base_name, model_class):

    @login_required
    def _generic_show(request, pk):

        edit_view = module.__name__ + '.views.' + base_name + '_edit'
        delete_view = module.__name__ + '.views.' + base_name + '_delete'
        log_view = module.__name__ + '.views.' + base_name + '_log'
        list_view = module.__name__ + '.views.' + base_name + '_list'

        obj = get_object_or_404(model_class, pk=pk, deleted=False)

        return render_to_response([module.__name__ + '/' + base_name + '/show.html', 'generic/generic/show.html'], {
            'Model': model_class, 'delete_view': delete_view, 'edit_view': edit_view, 'log_view': log_view, 'list_view': list_view,
            'obj': obj
        }, context_instance=RequestContext(request))

    return _generic_show


def generate_delete(module, base_name, model_class):

    @login_required
    def _generic_delete(request, pk):

        show_view = module.__name__ + '.views.' + base_name + '_show'
        list_view = module.__name__ + '.views.' + base_name + '_list'

        obj = get_object_or_404(model_class, pk=pk, deleted=False)

        if request.method == 'POST' and request.POST.get('do') == 'it':
            obj.deleted = True
            if hasattr(obj, 'delete_signal'):
                obj.delete_signal()
            obj.save()
            messages.success(request, _(u'Élément supprimé !'))
            return redirect(list_view)

        return render_to_response([module.__name__ + '/' + base_name + '/delete.html', 'generic/generic/delete.html'], {
            'Model': model_class, 'show_view': show_view, 'list_view': list_view,
            'obj': obj
        }, context_instance=RequestContext(request))

    return _generic_delete
