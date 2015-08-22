# from haystack import indexes
# from django.utils.timezone import now
#
# from vehicles.models import Booking
#
#
# class BookingIndex(indexes.SearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=True)
#     last_edit_date = indexes.DateTimeField()
#
#     def get_model(self):
#         return Booking
#
#     def index_queryset(self, using=None):
#         return self.get_model().objects.filter(deleted=False)
#
#     def prepare_last_edit_date(self, obj):
#         try:
#             return obj.last_log().when
#         except:
#             return now()
