from django import template

register = template.Library()


@register.inclusion_tag('main/templatetags/menu.html')
def display_links_for_menu(key):

    from main.models import Link

    menus = Link.objects.filter(leftmenu=key, deleted=False).order_by('title')

    return {'menus': menus}
