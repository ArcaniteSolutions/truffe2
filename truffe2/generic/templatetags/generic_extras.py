from django import template

register = template.Library()


@register.filter
def get_attr(value, arg):
    v = getattr(value, arg, None)
    if hasattr(v, '__call__'):
        v = v()
    if not v:
        return ''
    return v
