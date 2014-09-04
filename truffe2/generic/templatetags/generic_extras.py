from django import template
import re

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
