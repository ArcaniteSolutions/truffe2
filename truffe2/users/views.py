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


from users.models import TruffeUser, UserPrivacy
from users.forms import TruffeUserForm


import phonenumbers
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from django.db.models import Q


def login(request):
    """View to display the login page"""

    why = request.GET.get('why')

    return render_to_response('users/login/login.html', {'why': why}, context_instance=RequestContext(request))


@login_required
def users_list(request):
    """Display the list of users"""

    return render_to_response('users/users/list.html', {}, context_instance=RequestContext(request))


@login_required
def users_profile(request, pk):
    """Display a user profile"""

    user = get_object_or_404(TruffeUser, pk=pk)

    privacy_values = {}

    for field in UserPrivacy.FIELD_CHOICES:
        privacy_values[field[0]] = UserPrivacy.user_can_access(request.user, user, field[0])

    return render_to_response('users/users/profile.html', {'user_to_display': user, 'privacy_values': privacy_values}, context_instance=RequestContext(request))


class UserListJson(BaseDatatableView):
    model = TruffeUser

    columns = ['username', 'first_name', 'last_name', 'member_of', 'pk']
    order_columns = ['username', 'first_name', 'last_name', 'pk', 'pk']

    max_display_length = 500

    def render_column(self, row, column):
        if column == 'member_of':
            return 'Todo'
        else:
            return escape(super(UserListJson, self).render_column(row, column))

    def filter_queryset(self, qs):
        sSearch = self.request.POST.get('sSearch', None)
        if sSearch:
            qs = qs.filter(Q(first_name__istartswith=sSearch) | Q(last_name__istartswith=sSearch) | Q(username__istartswith=sSearch))
        return qs


@login_required
def users_edit(request, pk):
    """Edit a user profile"""

    user = get_object_or_404(TruffeUser, pk=pk)

    if not request.user.is_superuser and not user.pk == request.user.pk:
        raise Http404

    if request.method == 'POST':  # If the form has been submitted...
        form = TruffeUserForm(request.user, request.POST, instance=user)

        privacy_values = {}

        for field in UserPrivacy.FIELD_CHOICES:
            privacy_values[field[0]] = request.POST.get('priv_val_' + field[0])

        if form.is_valid():  # If the form is valid
            user = form.save()

            if user.mobile:
                user.mobile = phonenumbers.format_number(phonenumbers.parse(user.mobile, "CH"), phonenumbers.PhoneNumberFormat.E164)
                user.save()

            for (field, value) in privacy_values.iteritems():
                # At this point, the object should exist !
                UserPrivacy.objects.filter(user=user, field=field).update(level=value)

            messages.success(request, _(u'Profile sauvegardé !'))

            return redirect('users.views.users_profile', pk=user.pk)
    else:
        form = TruffeUserForm(request.user, instance=user)

        privacy_values = {}

        for field in UserPrivacy.FIELD_CHOICES:
            privacy_values[field[0]] = UserPrivacy.get_privacy_for_field(user, field[0])

    privacy_choices = UserPrivacy.LEVEL_CHOICES

    return render_to_response('users/users/edit.html', {'form': form, 'privacy_choices': privacy_choices, 'privacy_values': privacy_values}, context_instance=RequestContext(request))


@login_required
def users_vcard(request, pk):
    """Return a user vcard"""

    user = get_object_or_404(TruffeUser, pk=pk)

    retour = user.generate_vcard(request.user)

    response = HttpResponse(retour, content_type='text/x-vcard')
    nom = smart_str(user.get_full_name())
    nom = nom.replace(' ', '_')
    response['Content-Disposition'] = 'attachment; filename=' + nom + '.vcf'

    return response


@login_required
def users_set_body(request, mode):
    """Set the user mode for the body, keeping it consistent between requests"""

    request.user.body = mode
    request.user.save()

    return HttpResponse('')
