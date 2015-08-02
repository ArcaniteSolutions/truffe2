# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Renaming field 'ExpenseClaim.account_id'
        db.rename_column(u'accounting_main_budgetline', 'compte_id', 'account_id')

    def backwards(self, orm):
        # Renaming field 'ExpenseClaim.compte_id'
        db.rename_column(u'accounting_main_budgetline', 'account_id', 'compte_id')


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
        u'accounting_main.accountingerror': {
            'Meta': {'object_name': 'AccountingError'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_remark': ('django.db.models.fields.TextField', [], {}),
            'linked_line': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_main.AccountingLine']", 'null': 'True', 'blank': 'True'}),
            'linked_line_cache': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_drafting'", 'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'accounting_main.accountingerrorlogging': {
            'Meta': {'object_name': 'AccountingErrorLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_main.AccountingError']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_main.accountingerrormessage': {
            'Meta': {'object_name': 'AccountingErrorMessage'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"}),
            'error': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_main.AccountingError']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'accounting_main.accountingline': {
            'Meta': {'object_name': 'AccountingLine'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.Account']"}),
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'current_sum': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'document_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'output': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_imported'", 'max_length': '255'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'tva': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'accounting_main.accountinglinelogging': {
            'Meta': {'object_name': 'AccountingLineLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_main.AccountingLine']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'accounting_main.budget': {
            'Meta': {'object_name': 'Budget'},
            'accounting_year': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.AccountingYear']"}),
            'costcenter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.CostCenter']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'accounting_main.budgetline': {
            'Meta': {'object_name': 'BudgetLine'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_core.Account']"}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '2'}),
            'budget': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounting_main.Budget']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'accounting_main.budgetlogging': {
            'Meta': {'object_name': 'BudgetLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['accounting_main.Budget']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
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

    complete_apps = ['accounting_main']