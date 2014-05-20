
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
        current_unit = Unit.objects.get(pk=1)

    return current_unit


def update_current_unit(request, unit_pk):
    """Update the current unit"""

    request.session['current_unit_pk'] = unit_pk
