from django import template
from django.template.base import Node, NodeList

from rights.utils import ModelWithRight

from app.utils import get_current_unit, get_current_year

import importlib


register = template.Library()


class IfHasRightNode(Node):

    def __init__(self, conditions_nodelists):
        self.conditions_nodelists = conditions_nodelists

    def __repr__(self):
        return "<IfHRNode>"

    def __iter__(self):
        for _, nodelist in self.conditions_nodelists:
            for node in nodelist:

                yield node

    @property
    def nodelist(self):
        return NodeList(node for _, nodelist in self.conditions_nodelists for node in nodelist)

    def render(self, context):
        for (obj, user, right), nodelist in self.conditions_nodelists:

            if right is not None:  # if / elif clause
                obj = template.Variable(obj).resolve(context)
                user = template.Variable(user).resolve(context)
                right = template.Variable(right).resolve(context)

                if isinstance(obj, basestring):
                    new_obj = importlib.import_module('.'.join(obj.split('.')[:-1]))
                    obj = getattr(new_obj, obj.split('.')[-1])

                force_static = False

                if right[0] == '!':
                    force_static = True
                    right = right[1:]

                if isinstance(obj, ModelWithRight) and not force_static:
                    match = obj.rights_can(right, user)
                elif hasattr(obj, 'static_rights_can'):
                    match = obj.static_rights_can(right, user, get_current_unit(context['request']) if force_static else None, get_current_year(context['request']) if force_static else None)
                else:
                    raise Exception("?", obj, " cannot be used for rights")

            else:
                match = True

            if match:
                return nodelist.render(context)
        return ''


@register.tag('ifhasright')
def do_if_hr(parser, token):
    # {% if ... %}
    (obj, user, right) = token.split_contents()[1:]
    nodelist = parser.parse(('elifhasright', 'elsehasright', 'endifhasright'))
    conditions_nodelists = [((obj, user, right), nodelist)]
    token = parser.next_token()

    # {% elif ... %} (repeatable)
    while token.contents.startswith('elifhasright'):
        (obj, user, right) = token.split_contents()[1:]
        nodelist = parser.parse(('elifhasright', 'elsehasright', 'endifhasright'))
        conditions_nodelists.append(((obj, user, right), nodelist))
        token = parser.next_token()

    # {% else %} (optional)
    if token.contents == 'elsehasright':
        nodelist = parser.parse(('endifhasright',))
        conditions_nodelists.append(((None, None, None), nodelist))
        token = parser.next_token()

    # {% endif %}
    assert token.contents == 'endifhasright'

    return IfHasRightNode(conditions_nodelists)


class IfCanDisplayNode(Node):

    def __init__(self, conditions_nodelists):
        self.conditions_nodelists = conditions_nodelists

    def __repr__(self):
        return "<IfCDNode>"

    def __iter__(self):
        for _, nodelist in self.conditions_nodelists:
            for node in nodelist:
                yield node

    @property
    def nodelist(self):
        return NodeList(node for _, nodelist in self.conditions_nodelists for node in nodelist)

    def render(self, context):
        for (obj, user, field), nodelist in self.conditions_nodelists:

            if field is not None and hasattr(obj, 'MetaData') and hasattr(obj.MetaData, 'extra_right_display') and field in obj.MetaData.extra_right_display:  # if / elif clause
                obj = template.Variable(obj).resolve(context)
                user = template.Variable(user).resolve(context)
                field = template.Variable(field).resolve(context)

                if isinstance(obj, basestring):
                    new_obj = importlib.import_module('.'.join(obj.split('.')[:-1]))
                    obj = getattr(new_obj, obj.split('.')[-1])

                if isinstance(obj, ModelWithRight):
                    match = obj.MetaData.extra_right_display[field](obj, user)
                else:
                    raise Exception("?", obj, " cannot be used for rights")

            else:
                match = True

            if match:
                return nodelist.render(context)
        return ''


@register.tag('ifcandisplay')
def do_if_cd(parser, token):
    # {% if ... %}
    (obj, user, field) = token.split_contents()[1:]
    nodelist = parser.parse(('elifcandisplay', 'elsecandisplay', 'endifcandisplay'))
    conditions_nodelists = [((obj, user, field), nodelist)]
    token = parser.next_token()

    # {% elif ... %} (repeatable)
    while token.contents.startswith('elifcandisplay'):
        (obj, user, field) = token.split_contents()[1:]
        nodelist = parser.parse(('elifcandisplay', 'elsecandisplay', 'endifcandisplay'))
        conditions_nodelists.append(((obj, user, field), nodelist))
        token = parser.next_token()

    # {% else %} (optional)
    if token.contents == 'elsecandisplay':
        nodelist = parser.parse(('endifcandisplay',))
        conditions_nodelists.append(((None, None, None), nodelist))
        token = parser.next_token()

    # {% endif %}
    assert token.contents == 'endifcandisplay'

    return IfCanDisplayNode(conditions_nodelists)
