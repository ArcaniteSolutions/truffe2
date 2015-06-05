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
