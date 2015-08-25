# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.conf import settings


from app.utils import generate_pdf


@login_required
def booking_pdf(request, pk):

    from vehicles.models import Booking

    booking = get_object_or_404(Booking, pk=pk, deleted=False)

    if not booking.static_rights_can('SHOW', request.user):
        raise Http404

    return generate_pdf("vehicles/booking/pdf.html", request, {'object': booking})
