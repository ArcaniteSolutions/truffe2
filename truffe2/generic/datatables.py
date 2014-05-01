from django.db.models import Q
from django.template import RequestContext
from django.shortcuts import render_to_response


def generic_list_json(request, model, columns, templates):
    """Generic function for json list"""

    def do_ordering(qs):

        # Ordering
        try:
            i_sorting_cols = int(request.REQUEST.get('iSortingCols', 0))
        except ValueError:
            i_sorting_cols = 0

        order = []
        for i in range(i_sorting_cols):
            try:
                i_sort_col = int(request.REQUEST.get('iSortCol_%s' % i))
            except ValueError:
                i_sort_col = 0
            s_sort_dir = request.REQUEST.get('sSortDir_%s' % i)

            sdir = '-' if s_sort_dir == 'desc' else ''

            sortcol = columns[i_sort_col]
            if isinstance(sortcol, list):
                for sc in sortcol:
                    order.append('%s%s' % (sdir, sc))
            else:
                order.append('%s%s' % (sdir, sortcol))
        if order:
            qs = qs.order_by(*order)

        return qs

    def do_paging(qs):
        limit = min(int(request.REQUEST.get('iDisplayLength', 10)), 500)
        if limit == -1:
            return qs
        start = int(request.REQUEST.get('iDisplayStart', 0))
        offset = start + limit
        return qs[start:offset]

    def do_filtering(qs):
        sSearch = request.REQUEST.get('sSearch', None)
        if sSearch:
            base = Q(**{columns[0] + '__istartswith': sSearch})

            for col in columns[1:]:
                base = base | Q(**{col + '__istartswith': sSearch})

            qs = qs.filter(base)

        return qs

    qs = model.objects.all()

    total_records = qs.count()

    qs = do_filtering(qs)

    total_display_records = qs.count()

    qs = do_ordering(qs)
    qs = do_paging(qs)

    rep = render_to_response(templates, {'iTotalRecords': total_records, 'iTotalDisplayRecords': total_display_records, 'sEcho': int(request.REQUEST.get('sEcho', 0)), 'list': qs.all()}, context_instance=RequestContext(request), content_type='application/json')

    return rep
