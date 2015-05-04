from django import template
import re
import html5lib
from bleach.sanitizer import BleachSanitizer
from bleach.encoding import force_unicode
import bleach
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_attr(value, arg):
    v = getattr(value, arg, None)
    if hasattr(v, '__call__'):
        v = v()
    elif isinstance(value, dict):
        v = value.get(arg)
    if not v:
        return ''
    return v


pos = [(0, 0), (1, 0), (0, 1), (2, 3), (1, 2), (2, 1), (2, 2)]


@register.filter
def node_x(value):
    x, _ = pos[value]
    return x


@register.filter
def node_y(value):
    _, y = pos[value]
    return y


@register.simple_tag(takes_context=True)
def switchable(context, obj, user, id):
    return 'true' if obj.may_switch_to(user, id) else 'false'

re_spaceless = re.compile("(\n|\r)+")


@register.tag
def nocrlf(parser, token):
    nodelist = parser.parse(('endnocrlf',))
    parser.delete_first_token()
    return CrlfNode(nodelist)


class CrlfNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        rendered = self.nodelist.render(context).strip()
        return re_spaceless.sub("", rendered)


@register.filter
def html_check_and_safe(value):

    tags = bleach.ALLOWED_TAGS + ['br', 'font', 'p', 'table', 'tr', 'td', 'th', 'img', 'u', 'span', 'tbody', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']
    attrs = {
        '*': ['class', 'style', 'color', 'align'],
        'a': ['href', 'rel'],
        'img': ['src', 'alt'],
    }
    style = ['line-height', 'background-color', 'font-size']

    text = force_unicode(value)

    class s(BleachSanitizer):
        allowed_elements = tags
        allowed_attributes = attrs
        allowed_css_properties = style
        strip_disallowed_elements = True
        strip_html_comments = True
        allowed_protocols = ['http', 'https', 'data']

    parser = html5lib.HTMLParser(tokenizer=s)

    return mark_safe(bleach._render(parser.parseFragment(text)))
