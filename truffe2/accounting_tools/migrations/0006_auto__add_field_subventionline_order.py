# Python bytecode 2.7 (62211)
# Embedded file name: /var/www/git-repo/truffe2/truffe2/accounting_tools/migrations/0006_auto__add_field_subventionline_order.py
# Compiled at: 2015-07-04 20:37:00
# Decompiled by https://python-decompiler.com
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        db.add_column('accounting_tools_subventionline', 'order', self.gf('django.db.models.fields.SmallIntegerField')(4=0), 6=False)

    def backwards(self, orm):
        db.delete_column('accounting_tools_subventionline', 'order')

    models = {'accounting_core.accountingyear': {'Meta': {'object_name': 'AccountingYear'}, 'deleted': (
                                                    'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                                          'end_date': (
                                                     'django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}), 
                                          'id': (
                                               'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                                          'name': (
                                                 'django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}), 
                                          'start_date': (
                                                       'django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}), 
                                          'status': (
                                                   'django.db.models.fields.CharField', [], {'default': "'0_preparing'", 'max_length': '255'}), 
                                          'subvention_deadline': (
                                                                'django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})}, 
       'accounting_tools.subvention': {'Meta': {'unique_together': "(('unit', 'unit_blank_name', 'accounting_year'),)", 'object_name': 'Subvention'}, 'accounting_year': (
                                                         'django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting_core.AccountingYear']"}), 
                                       'amount_asked': (
                                                      'django.db.models.fields.SmallIntegerField', [], {}), 
                                       'amount_given': (
                                                      'django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}), 
                                       'comment_root': (
                                                      'django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}), 
                                       'deleted': (
                                                 'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                                       'description': (
                                                     'django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}), 
                                       'id': (
                                            'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                                       'kind': (
                                              'django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}), 
                                       'mobility_asked': (
                                                        'django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}), 
                                       'mobility_given': (
                                                        'django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}), 
                                       'name': (
                                              'django.db.models.fields.CharField', [], {'max_length': '255'}), 
                                       'status': (
                                                'django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}), 
                                       'unit': (
                                              'django.db.models.fields.related.ForeignKey', [], {'to': "orm['units.Unit']", 'null': 'True', 'blank': 'True'}), 
                                       'unit_blank_name': (
                                                         'django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}), 
                                       'unit_blank_user': (
                                                         'django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.TruffeUser']", 'null': 'True', 'blank': 'True'})}, 
       'accounting_tools.subventionfile': {'Meta': {'object_name': 'SubventionFile'}, 'file': (
                                                  'django.db.models.fields.files.FileField', [], {'max_length': '100'}), 
                                           'id': (
                                                'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                                           'object': (
                                                    'django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'files'", 'null': 'True', 'to': "orm['accounting_tools.Subvention']"}), 
                                           'upload_date': (
                                                         'django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}), 
                                           'uploader': (
                                                      'django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.TruffeUser']"})}, 
       'accounting_tools.subventionline': {'Meta': {'object_name': 'SubventionLine'}, 'end_date': (
                                                      'django.db.models.fields.DateField', [], {}), 
                                           'id': (
                                                'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                                           'name': (
                                                  'django.db.models.fields.CharField', [], {'max_length': '255'}), 
                                           'nb_spec': (
                                                     'django.db.models.fields.SmallIntegerField', [], {}), 
                                           'order': (
                                                   'django.db.models.fields.SmallIntegerField', [], {}), 
                                           'place': (
                                                   'django.db.models.fields.CharField', [], {'max_length': '100'}), 
                                           'start_date': (
                                                        'django.db.models.fields.DateField', [], {}), 
                                           'subvention': (
                                                        'django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['accounting_tools.Subvention']"})}, 
       'accounting_tools.subventionlogging': {'Meta': {'object_name': 'SubventionLogging'}, 'extra_data': (
                                                           'django.db.models.fields.TextField', [], {'blank': 'True'}), 
                                              'id': (
                                                   'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                                              'object': (
                                                       'django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': "orm['accounting_tools.Subvention']"}), 
                                              'what': (
                                                     'django.db.models.fields.CharField', [], {'max_length': '64'}), 
                                              'when': (
                                                     'django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}), 
                                              'who': (
                                                    'django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.TruffeUser']"})}, 
       'auth.group': {'Meta': {'object_name': 'Group'}, 'id': (
                           'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                      'name': (
                             'django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}), 
                      'permissions': (
                                    'django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})}, 
       'auth.permission': {'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'}, 'codename': (
                                      'django.db.models.fields.CharField', [], {'max_length': '100'}), 
                           'content_type': (
                                          'django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}), 
                           'id': (
                                'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                           'name': (
                                  'django.db.models.fields.CharField', [], {'max_length': '50'})}, 
       'contenttypes.contenttype': {'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"}, 'app_label': (
                                                'django.db.models.fields.CharField', [], {'max_length': '100'}), 
                                    'id': (
                                         'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                                    'model': (
                                            'django.db.models.fields.CharField', [], {'max_length': '100'}), 
                                    'name': (
                                           'django.db.models.fields.CharField', [], {'max_length': '100'})}, 
       'units.unit': {'Meta': {'object_name': 'Unit'}, 'deleted': (
                                'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                      'description': (
                                    'django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}), 
                      'id': (
                           'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                      'id_epfl': (
                                'django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}), 
                      'is_commission': (
                                      'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                      'is_equipe': (
                                  'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                      'is_hidden': (
                                  'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                      'name': (
                             'django.db.models.fields.CharField', [], {'max_length': '255'}), 
                      'parent_hierarchique': (
                                            'django.db.models.fields.related.ForeignKey', [], {'to': "orm['units.Unit']", 'null': 'True', 'blank': 'True'}), 
                      'url': (
                            'django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})}, 
       'users.truffeuser': {'Meta': {'object_name': 'TruffeUser'}, 'adresse': (
                                      'django.db.models.fields.TextField', [], {'blank': 'True'}), 
                            'body': (
                                   'django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '1'}), 
                            'date_joined': (
                                          'django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}), 
                            'email': (
                                    'django.db.models.fields.EmailField', [], {'max_length': '255'}), 
                            'email_perso': (
                                          'django.db.models.fields.EmailField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}), 
                            'first_name': (
                                         'django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}), 
                            'groups': (
                                     'django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': "orm['auth.Group']"}), 
                            'iban_ou_ccp': (
                                          'django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}), 
                            'id': (
                                 'django.db.models.fields.AutoField', [], {'primary_key': 'True'}), 
                            'is_active': (
                                        'django.db.models.fields.BooleanField', [], {'default': 'True'}), 
                            'is_superuser': (
                                           'django.db.models.fields.BooleanField', [], {'default': 'False'}), 
                            'last_login': (
                                         'django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}), 
                            'last_name': (
                                        'django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}), 
                            'mobile': (
                                     'django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}), 
                            'nom_banque': (
                                         'django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}), 
                            'password': (
                                       'django.db.models.fields.CharField', [], {'max_length': '128'}), 
                            'user_permissions': (
                                               'django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']"}), 
                            'username': (
                                       'django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})}}
    complete_apps = [
     'accounting_tools']
