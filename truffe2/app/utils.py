from django.conf import settings

def add_current_unit(request):
    """Template context processor to add current unit"""

    return {'CURRENT_UNIT': get_current_unit(request)}


def get_current_unit(request):
    """Return the current unit"""

    from units.models import Unit

    current_unit_pk = request.session.get('current_unit_pk', 1)

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

    request.session['current_unit_pk'] = unit_pk


from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.contrib.sites.models import get_current_site


def send_templated_mail(request, subject, email_from, emails_to, template, context):
    """Send a email using an template (both in text and html format)"""

    plaintext = get_template('%s_plain.txt' % (template, ))
    htmly = get_template('%s_html.html' % (template, ))

    context.update({'site': get_current_site(request)})

    d = Context(context)
    text_content = plaintext.render(d)
    html_content = htmly.render(d)

    msg = EmailMultiAlternatives(subject, text_content, email_from, emails_to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
