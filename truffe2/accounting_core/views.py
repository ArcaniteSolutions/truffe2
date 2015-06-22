# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _

from app.utils import update_current_year


@login_required
def copy_accounting_year(request, pk):
    from accounting_core.models import AccountingYear, AccountCategory

    accounting_year = get_object_or_404(AccountingYear, pk=pk)
    if not accounting_year.rights_can('EDIT', request.user):
        raise Http404

    account_categories = accounting_year.accountcategory_set.all()
    accounts = accounting_year.account_set.all()
    cost_centers = accounting_year.costcenter_set.all()

    accounting_year.name = 'Copy of {}'.format(accounting_year.name)
    accounting_year.id = None
    accounting_year.save()

    copiable_objects = (account_categories, accounts, cost_centers)
    for idx in range(len(copiable_objects)):
        liste = copiable_objects[idx]

        # Create the new objects
        for elem in liste:
            elem.accounting_year = accounting_year
            elem.id = None
            elem.save()

        if idx == 2:
            break

        # Correct dependencies on the new objects
        field_name = 'parent_hierarchique' if idx == 0 else 'category'
        for elem in liste:
            if getattr(elem, field_name):  # if it was None, remains None
                setattr(elem, field_name, AccountCategory.objects.get(accounting_year=accounting_year, name=getattr(elem, field_name).name))
                elem.save()

    messages.success(request, _(u'Copie terminée avec succès'))
    update_current_year(request, accounting_year.pk)
    return redirect('accounting_core.views.accountingyear_edit', accounting_year.pk)
