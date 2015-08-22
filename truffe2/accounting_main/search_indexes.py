# from haystack import indexes
# from django.utils.timezone import now
#
# from accounting_main.models import AccountingLine
#
#
# class AccountingLineIndex(indexes.SearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=True)
#     last_edit_date = indexes.DateTimeField()
#
#     def get_model(self):
#         return AccountingLine
#
#     def index_queryset(self, using=None):
#         return self.get_model().objects.filter(deleted=False)
#
#     def prepare_last_edit_date(self, obj):
#         try:
#             return obj.last_log().when
#         except:
#             return now()
