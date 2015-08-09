from django.db.models import Q
from django.template import RequestContext
from django.shortcuts import render


def generic_list_json(request, model, columns, templates, bonus_data={}, check_deleted=False, filter_fields=[], bonus_filter_function=None, bonus_filter_function_with_parameters=None, deca_one_status=False, not_sortable_colums=[], selector_column=False, columns_mapping=None):
    """Generic function for json list"""

    if not filter_fields:
        filter_fields = columns

    not_sortable_colums_local = not_sortable_colums + (model.MetaData.not_sortable_colums if hasattr(model, 'MetaData') and hasattr(model.MetaData, 'not_sortable_colums') else [])
    columns_mapping_local = model.MetaData.trans_sort if hasattr(model, 'MetaData') and hasattr(model.MetaData, 'trans_sort') else (columns_mapping or {})

    def do_ordering(qs):

        # Ordering
        try:
            i_sorting_cols = int(request.REQUEST.get('iSortingCols', 0))
        except:
            i_sorting_cols = 0

        order = []
        for i in range(i_sorting_cols):
            try:
                i_sort_col = int(request.REQUEST.get('iSortCol_%s' % i))
            except ValueError:
                i_sort_col = 0
            s_sort_dir = request.REQUEST.get('sSortDir_%s' % i)

            sdir = '-' if s_sort_dir == 'desc' else ''

            sortcol = columns[i_sort_col + (-1 if selector_column else 0)]

            if isinstance(sortcol, list):
                for sc in sortcol:
                    if sc not in not_sortable_colums_local:
                        order.append('%s%s' % (sdir, columns_mapping_local.get(sc, sc)))
            else:
                if sortcol not in not_sortable_colums_local:
                    order.append('%s%s' % (sdir, columns_mapping_local.get(sortcol, sortcol)))

        if '-pk' not in order and 'pk' not in order:
            order.append('-pk')

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
            base = Q(**{filter_fields[0] + '__icontains': sSearch})

            for col in filter_fields[1:]:
                base = base | Q(**{col + '__icontains': sSearch})

            qs = qs.filter(base)

        if hasattr(model, 'MetaState') and hasattr(model.MetaState, 'status_col_id'):
            status_search = request.REQUEST.get('sSearch_%s' % (model.MetaState.status_col_id + (0 if not deca_one_status else 0) + (0 if selector_column else 0),), None)

            if status_search == "null":
                status_search = None

            if status_search:
                status_search_splited = status_search.split(',')

                base = Q(status=status_search_splited[0])

                for v in status_search_splited[1:]:
                    base = base | Q(status=v)

                qs = qs.filter(base)

        if bonus_filter_function:
            qs = bonus_filter_function(qs)

        if bonus_filter_function_with_parameters:
            qs = bonus_filter_function_with_parameters(qs, request)

        return qs

    qs = model.objects.all()

    if check_deleted:
        qs = qs.filter(deleted=False).all()

    total_records = qs.count()

    qs = do_filtering(qs)

    total_display_records = qs.count()

    qs = do_ordering(qs)
    qs = do_paging(qs)

    data = {'iTotalRecords': total_records, 'iTotalDisplayRecords': total_display_records, 'sEcho': int(request.REQUEST.get('sEcho', 0)), 'list': qs.all()}
    data.update(bonus_data)

    rep = render(request, templates, data, content_type='application/json')

    return rep
