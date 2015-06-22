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

    accounting_years = [get_object_or_404(AccountingYear, pk=pk_) for pk_ in filter(lambda x: x, pk.split(','))]

    for ay in accounting_years:
        if not ay.rights_can('EDIT', request.user):
            raise Http404

        account_categories = ay.accountcategory_set.all()
        accounts = ay.account_set.all()
        cost_centers = ay.costcenter_set.all()

        ay.name = 'Copy of {}'.format(ay.name)
        ay.id = None
        ay.save()

        copiable_objects = (account_categories, accounts, cost_centers)
        for idx in range(len(copiable_objects)):
            liste = copiable_objects[idx]

            # Create the new objects
            for elem in liste:
                elem.accounting_year = ay
                elem.id = None
                elem.save()

            if idx == 2:
                break

            # Correct dependencies on the new objects
            field_name = 'parent_hierarchique' if idx == 0 else 'category'
            for elem in liste:
                if getattr(elem, field_name):  # if it was None, remains None
                    setattr(elem, field_name, AccountCategory.objects.get(accounting_year=ay, name=getattr(elem, field_name).name))
                    elem.save()

    messages.success(request, _(u'Copie terminée avec succès'))

    if len(accounting_years) == 1:
        update_current_year(request, accounting_years[0].pk)
        return redirect('accounting_core.views.accountingyear_edit', accounting_years[0].pk)
    else:
        return redirect('accounting_core.views.accountingyear_list')
