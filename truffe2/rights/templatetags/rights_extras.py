from django import template
from django.template.base import Node, NodeList

from rights.utils import BasicRightModel

register = template.Library()


class IfHasRightNode(Node):

    def __init__(self, conditions_nodelists):
        self.conditions_nodelists = conditions_nodelists

    def __repr__(self):
        return "<IfNode>"

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

                if isinstance(obj, BasicRightModel):
                    match = obj.rights_can(right, user)
                elif hasattr(obj, 'static_rights_can'):
                    match = obj.static_rights_can(right, user)
                else:
                    match = True

            else:
                match = True

            if match:
                return nodelist.render(context)
        return ''


@register.tag('ifhasright')
def do_if(parser, token):
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
