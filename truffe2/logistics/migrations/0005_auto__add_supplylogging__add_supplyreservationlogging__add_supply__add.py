# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SupplyLogging'
        db.create_table(u'logistics_supplylogging', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('when', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('extra_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('who', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.TruffeUser'])),
            ('what', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(related_name='logs', to=orm['logistics.Supply'])),
        ))
        db.send_create_signal(u'logistics', ['SupplyLogging'])

        # Adding model 'SupplyReservationLogging'
        db.create_table(u'logistics_supplyreservationlogging', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('when', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('extra_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('who', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.TruffeUser'])),
            ('what', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(related_name='logs', to=orm['logistics.SupplyReservation'])),
        ))
        db.send_create_signal(u'logistics', ['SupplyReservationLogging'])

        # Adding model 'Supply'
        db.create_table(u'logistics_supply', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('conditions', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('allow_externals', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('conditions_externals', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('max_days', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('max_days_externals', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('minimum_days_before', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('minimum_days_before_externals', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('maximum_days_before', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('maximum_days_before_externals', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['units.Unit'])),
        ))
        db.send_create_signal(u'logistics', ['Supply'])

        # Adding model 'SupplyReservation'
        db.create_table(u'logistics_supplyreservation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('raison', self.gf('django.db.models.fields.TextField')()),
            ('remarks', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='0_draft', max_length=255)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['units.Unit'], null=True, blank=True)),
            ('unit_blank_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.TruffeUser'], null=True, blank=True)),
            ('unit_blank_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('supply', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.Supply'])),
        ))
        db.send_create_signal(u'logistics', ['SupplyReservation'])


    def backwards(self, orm):
        # Deleting model 'SupplyLogging'
        db.delete_table(u'logistics_supplylogging')

        # Deleting model 'SupplyReservationLogging'
        db.delete_table(u'logistics_supplyreservationlogging')

        # Deleting model 'Supply'
        db.delete_table(u'logistics_supply')

        # Deleting model 'SupplyReservation'
        db.delete_table(u'logistics_supplyreservation')


    models = {
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
        u'logistics.room': {
            'Meta': {'object_name': 'Room'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'allow_externals': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'conditions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'conditions_externals': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_days': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'max_days_externals': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'maximum_days_before': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'maximum_days_before_externals': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'minimum_days_before': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'minimum_days_before_externals': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'logistics.roomlogging': {
            'Meta': {'object_name': 'RoomLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['logistics.Room']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'logistics.roomreservation': {
            'Meta': {'object_name': 'RoomReservation'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raison': ('django.db.models.fields.TextField', [], {}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['logistics.Room']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']", 'null': 'True', 'blank': 'True'}),
            'unit_blank_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'unit_blank_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']", 'null': 'True', 'blank': 'True'})
        },
        u'logistics.roomreservationlogging': {
            'Meta': {'object_name': 'RoomReservationLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['logistics.RoomReservation']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'logistics.supply': {
            'Meta': {'object_name': 'Supply'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'allow_externals': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'conditions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'conditions_externals': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_days': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'max_days_externals': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'maximum_days_before': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'maximum_days_before_externals': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'minimum_days_before': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'minimum_days_before_externals': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"})
        },
        u'logistics.supplylogging': {
            'Meta': {'object_name': 'SupplyLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['logistics.Supply']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'logistics.supplyreservation': {
            'Meta': {'object_name': 'SupplyReservation'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raison': ('django.db.models.fields.TextField', [], {}),
            'remarks': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'supply': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['logistics.Supply']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']", 'null': 'True', 'blank': 'True'}),
            'unit_blank_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'unit_blank_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']", 'null': 'True', 'blank': 'True'})
        },
        u'logistics.supplyreservationlogging': {
            'Meta': {'object_name': 'SupplyReservationLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['logistics.SupplyReservation']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'units.unit': {
            'Meta': {'object_name': 'Unit'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_epfl': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'is_commission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_equipe': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent_herachique': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']", 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'users.truffeuser': {
            'Meta': {'object_name': 'TruffeUser'},
            'adresse': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body': ('django.db.models.fields.CharField', [], {'default': "'.'", 'max_length': '1'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
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

    complete_apps = ['logistics']