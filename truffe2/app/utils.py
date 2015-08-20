# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.template.loader import get_template
from django.template import Context
from django import http
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils.timezone import now
from django.contrib.sites.models import get_current_site

import cgi
import ho.pisa as pisa
import cStringIO as StringIO


def add_current_unit(request):
    """Template context processor to add current unit"""

    current_unit = get_current_unit(request, True, True)

    current_unit_pk = current_unit.pk if current_unit else -1
    current_unit_name = current_unit.name if current_unit else _(u'Unités externes')

    return {'CURRENT_UNIT': current_unit, 'CURRENT_UNIT_NAME': current_unit_name, 'CURRENT_UNIT_PK': current_unit_pk}


def get_current_unit(request, unit_blank=True, allow_all_units=False):
    """Return the current unit"""

    from units.models import Unit

    current_unit_pk = request.session.get('current_unit_pk', 1)

    try:
        if int(current_unit_pk) == -1 and unit_blank:
            return None
    except:
        pass

    try:
        if int(current_unit_pk) == -2 and allow_all_units:
            return Unit(name=_(u'Toutes les unités'), pk=-2)
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


def has_property(obj, prop):

    for attr in prop.split('.'):
        if not hasattr(obj, attr):
            return False
        obj = getattr(obj, attr)

    return True


def set_property(obj, prop, val):

    for attr in prop.split('.')[:-1]:
        if not hasattr(obj, attr):
            raise AttributeError('Attribute {} of {} not found in {}'.format(attr, prop, obj))
        obj = getattr(obj, attr)

    setattr(obj, prop.split('.')[-1], val)


def generate_pdf(template, request, contexte):
    template = get_template(template)
    contexte.update({'MEDIA_ROOT': settings.MEDIA_ROOT, 'cdate': now(), 'user': request.user})
    context = Context(contexte)

    html = template.render(context)

    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return http.HttpResponse(result.getvalue(), mimetype='application/pdf')

    return http.HttpResponse('Gremlins ate your pdf! %s' % cgi.escape(html))


def pad_image(image, **kwargs):
    """ Pad an image to make it the same aspect ratio of the desired thumbnail.
    """

    img_size = image.size
    des_size = kwargs['size']
    fit = [float(img_size[i]) / des_size[i] for i in range(0, 2)]

    if fit[0] > fit[1]:
        new_image = image.resize((image.size[0], int(round(des_size[1] * fit[0]))))
        top = int((new_image.size[1] - image.size[1]) / 2)
        left = 0
    elif fit[0] < fit[1]:
        new_image = image.resize((int(round(des_size[0] * fit[1])), image.size[1]))
        top = 0
        left = int((new_image.size[0] - image.size[0]) / 2)
    else:
        return image

    # For white
    new_image.paste((255, 255, 255, 255))

    new_image.paste(image, (left, top))
    return new_image
