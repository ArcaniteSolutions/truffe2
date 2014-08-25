from django import template
import re

register = template.Library()


@register.filter
def get_attr(value, arg):
    v = getattr(value, arg, None)
    if hasattr(v, '__call__'):
        v = v()
    if not v:
        return ''
    return v


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
