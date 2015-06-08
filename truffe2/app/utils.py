# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


def add_current_unit(request):
    """Template context processor to add current unit"""

    current_unit = get_current_unit(request, True)

    current_unit_pk = current_unit.pk if current_unit else -1
    current_unit_name = current_unit.name if current_unit else _(u'Unités externes')

    return {'CURRENT_UNIT': current_unit, 'CURRENT_UNIT_NAME': current_unit_name, 'CURRENT_UNIT_PK': current_unit_pk}


def get_current_unit(request, unit_blank=True):
    """Return the current unit"""

    from units.models import Unit

    current_unit_pk = request.session.get('current_unit_pk', 1)

    try:
        if int(current_unit_pk) == -1 and unit_blank:
            return None
    except:
        pass

    try:
        current_unit = Unit.objects.get(pk=current_unit_pk)
    except Unit.DoesNotExist:
        try:
            current_unit = Unit.objects.get(pk=settings.ROOT_UNIT_PK)
        except:
            current_unit = None

    return current_unit


def update_current_unit(request, unit_pk):
    """Update the current unit"""

    if request.GET.get('_upkns') == '_':
        return

    request.session['current_unit_pk'] = unit_pk


def add_current_year(request):
    """Template context processor to add current year"""

    from accounting_core.models import AccountingYear

    current_year = get_current_year(request)

    current_year_pk = current_year.pk if current_year else -1
    current_year_name = current_year.name if current_year else _(u'?')

    return {'CURRENT_YEAR': current_year, 'CURRENT_YEAR_NAME': current_year_name, 'CURRENT_YEAR_PK': current_year_pk}


def get_current_year(request):
    """Return the current year"""

    from accounting_core.models import AccountingYear

    current_year_pk = request.session.get('current_year_pk')

    try:
        current_year = AccountingYear.objects.get(pk=current_year_pk)
    except AccountingYear.DoesNotExist:
        try:
            current_year = AccountingYear.objects.filter(status='1_active').first()
        except:
            current_year = None

    return current_year


def update_current_year(request, year_pk):
    """Update the current year"""

    if request.GET.get('_ypkns') == '_':
        return

    request.session['current_year_pk'] = year_pk


from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.contrib.sites.models import get_current_site


def send_templated_mail(request, subject, email_from, emails_to, template, context):
    """Send a email using an template (both in text and html format)"""

    plaintext = get_template('%s_plain.txt' % (template, ))
    htmly = get_template('%s_html.html' % (template, ))

    context.update({'site': get_current_site(request), 'subject': subject})

    d = Context(context)
    text_content = plaintext.render(d)
    html_content = htmly.render(d)

    msg = EmailMultiAlternatives(subject, text_content, email_from, emails_to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def get_property(obj, prop):

    for attr in prop.split('.'):
        if not hasattr(obj, attr):
            return None
        obj = getattr(obj, attr)

    return obj
