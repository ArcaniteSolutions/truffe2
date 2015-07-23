# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CashBookFile'
        db.create_table(u'accounting_tools_cashbookfile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('uploader', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.TruffeUser'])),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='files', null=True, to=orm['accounting_tools.CashBook'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal(u'accounting_tools', ['CashBookFile'])

        # Adding model 'CashBook'
        db.create_table(u'accounting_tools_cashbook', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.TruffeUser'])),
            ('nb_proofs', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('status', self.gf('django.db.models.fields.CharField')(default='0_draft', max_length=255)),
            ('accounting_year', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting_core.AccountingYear'])),
            ('costcenter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting_core.CostCenter'])),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['units.Unit'])),
        ))
        db.send_create_signal(u'accounting_tools', ['CashBook'])

        # Adding model 'CashBookLogging'
        db.create_table(u'accounting_tools_cashbooklogging', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('when', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('extra_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('who', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.TruffeUser'])),
            ('what', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(related_name='logs', to=orm['accounting_tools.CashBook'])),
        ))
        db.send_create_signal(u'accounting_tools', ['CashBookLogging'])

        # Adding model 'CashBookLine'
        db.create_table(u'accounting_tools_cashbookline', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('cashbook', self.gf('django.db.models.fields.related.ForeignKey')(related_name='lines', to=orm['accounting_tools.CashBook'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('helper', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('proof', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting_core.Account'])),
            ('value', self.gf('django.db.models.fields.DecimalField')(max_digits=20, decimal_places=2)),
            ('tva', self.gf('django.db.models.fields.DecimalField')(max_digits=20, decimal_places=2)),
            ('value_ttc', self.gf('django.db.models.fields.DecimalField')(max_digits=20, decimal_places=2)),
        ))
        db.send_create_signal(u'accounting_tools', ['CashBookLine'])


    def backwards(self, orm):
        # Deleting model 'CashBookFile'
        db.delete_table(u'accounting_tools_cashbookfile')

        # Deleting model 'CashBook'
        db.delete_table(u'accounting_tools_cashbook')

        # Deleting model 'CashBookLogging'
        db.delete_table(u'accounting_tools_cashbooklogging')

        # Deleting model 'CashBookLine'
        db.delete_table(u'accounting_tools_cashbookline')


    models = {
        u'accounting_core.account': {
            'Meta': {'unique_together': "(('name', 'accounting_year'), ('account_number', 'accounting_year'))", 'object_name': 'Account'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountCategory']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'visibility': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'accounting_core.accountcategory': {
            'Meta': {'unique_together': "(('name', 'accounting_year'),)", 'object_name': 'AccountCategory'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'parent_hierarchique': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountCategory']", 'null': 'True', 'blank': 'True'})
        },
        u'accounting_core.accountingyear': {
            'Meta': {'object_name': 'AccountingYear'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_preparing'", 'max_length': '255'}),
            'subvention_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'accounting_core.costcenter': {
            'Meta': {'unique_together': "(('name', 'accounting_year'), ('account_number', 'accounting_year'))", 'object_name': 'CostCenter'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'accounting_tools.cashbook': {
            'Meta': {'object_name': 'CashBook'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'nb_proofs': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.cashbookfile': {
            'Meta': {'object_name': 'CashBookFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'files'", 'null': 'True', 'to': u"orm['accounting_tools.CashBook']"}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.cashbookline': {
            'Meta': {'object_name': 'CashBookLine'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.Account']"}),
            'cashbook': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lines'", 'to': u"orm['accounting_tools.CashBook']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'helper': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'proof': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tva': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'value_ttc': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'})
        },
        u'accounting_tools.cashbooklogging': {
            'Meta': {'object_name': 'CashBookLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_tools.CashBook']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.expenseclaim': {
            'Meta': {'object_name': 'ExpenseClaim'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'nb_proofs': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.expenseclaimfile': {
            'Meta': {'object_name': 'ExpenseClaimFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'files'", 'null': 'True', 'to': u"orm['accounting_tools.ExpenseClaim']"}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.expenseclaimline': {
            'Meta': {'object_name': 'ExpenseClaimLine'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.Account']"}),
            'expense_claim': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lines'", 'to': u"orm['accounting_tools.ExpenseClaim']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'proof': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tva': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'value_ttc': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'})
        },
        u'accounting_tools.expenseclaimlogging': {
            'Meta': {'object_name': 'ExpenseClaimLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_tools.ExpenseClaim']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.internaltransfer': {
            'Meta': {'object_name': 'InternalTransfer'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.Account']"}),
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'cost_center_from': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'internal_transfer_from'", 'to': u"orm['accounting_core.CostCenter']"}),
            'cost_center_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'internal_transfer_to'", 'to': u"orm['accounting_core.CostCenter']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'})
        },
        u'accounting_tools.internaltransferlogging': {
            'Meta': {'object_name': 'InternalTransferLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_tools.InternalTransfer']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.internaltransfertag': {
            'Meta': {'object_name': 'InternalTransferTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['accounting_tools.InternalTransfer']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'accounting_tools.invoice': {
            'Meta': {'object_name': 'Invoice'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'annex': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'custom_bvr_number': ('django.db.models.fields.CharField', [], {'max_length': '59', 'null': 'True', 'blank': 'True'}),
            'date_and_place': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_account': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'display_bvr': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'ending': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'greetings': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'preface': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sign': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_preparing'", 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'accounting_tools.invoiceline': {
            'Meta': {'object_name': 'InvoiceLine'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lines'", 'to': u"orm['accounting_tools.Invoice']"}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'quantity': ('django.db.models.fields.DecimalField', [], {'default': '1', 'max_digits': '20', 'decimal_places': '0'}),
            'tva': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'value': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'value_ttc': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'})
        },
        u'accounting_tools.invoicelogging': {
            'Meta': {'object_name': 'InvoiceLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_tools.Invoice']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.invoicetag': {
            'Meta': {'object_name': 'InvoiceTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['accounting_tools.Invoice']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'accounting_tools.linkedinfo': {
            'Meta': {'object_name': 'LinkedInfo'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'bank': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'iban_ccp': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'accounting_tools.subvention': {
            'Meta': {'unique_together': "(('unit', 'unit_blank_name', 'accounting_year'),)", 'object_name': 'Subvention'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'amount_asked': ('django.db.models.fields.IntegerField', [], {}),
            'amount_given': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'comment_root': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'mobility_asked': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mobility_given': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']", 'null': 'True', 'blank': 'True'}),
            'unit_blank_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'unit_blank_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']", 'null': 'True', 'blank': 'True'})
        },
        u'accounting_tools.subventionfile': {
            'Meta': {'object_name': 'SubventionFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'files'", 'null': 'True', 'to': u"orm['accounting_tools.Subvention']"}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.subventionline': {
            'Meta': {'object_name': 'SubventionLine'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'nb_spec': ('django.db.models.fields.SmallIntegerField', [], {}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'place': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'subvention': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': u"orm['accounting_tools.Subvention']"})
        },
        u'accounting_tools.subventionlogging': {
            'Meta': {'object_name': 'SubventionLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_tools.Subvention']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.withdrawal': {
            'Meta': {'object_name': 'Withdrawal'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'desired_date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"}),
            'withdrawn_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'accounting_tools.withdrawalfile': {
            'Meta': {'object_name': 'WithdrawalFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'files'", 'null': 'True', 'to': u"orm['accounting_tools.Withdrawal']"}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.withdrawallogging': {
            'Meta': {'object_name': 'WithdrawalLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_tools.Withdrawal']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_tools.withdrawaltag': {
            'Meta': {'object_name': 'WithdrawalTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['accounting_tools.Withdrawal']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'units.unit': {
            'Meta': {'object_name': 'Unit'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_epfl': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'is_commission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_equipe': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent_hierarchique': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']", 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'users.truffeuser': {
            'Meta': {'object_name': 'TruffeUser'},
            'adresse': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '1'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'email_perso': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            'iban_ou_ccp': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'nom_banque': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['accounting_tools']