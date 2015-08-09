# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Booking.remark'
        db.alter_column(u'vehicles_booking', 'remark', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'Booking.remark_agepoly'
        db.alter_column(u'vehicles_booking', 'remark_agepoly', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'Booking.location'
        db.alter_column(u'vehicles_booking', 'location_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vehicles.Location'], null=True))

        # Changing field 'Booking.card'
        db.alter_column(u'vehicles_booking', 'card_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vehicles.Card'], null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Booking.remark'
        raise RuntimeError("Cannot reverse this migration. 'Booking.remark' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Booking.remark'
        db.alter_column(u'vehicles_booking', 'remark', self.gf('django.db.models.fields.TextField')())

        # User chose to not deal with backwards NULL issues for 'Booking.remark_agepoly'
        raise RuntimeError("Cannot reverse this migration. 'Booking.remark_agepoly' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Booking.remark_agepoly'
        db.alter_column(u'vehicles_booking', 'remark_agepoly', self.gf('django.db.models.fields.TextField')())

        # User chose to not deal with backwards NULL issues for 'Booking.location'
        raise RuntimeError("Cannot reverse this migration. 'Booking.location' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Booking.location'
        db.alter_column(u'vehicles_booking', 'location_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vehicles.Location']))

        # User chose to not deal with backwards NULL issues for 'Booking.card'
        raise RuntimeError("Cannot reverse this migration. 'Booking.card' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Booking.card'
        db.alter_column(u'vehicles_booking', 'card_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vehicles.Card']))

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
            'is_betatester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'nom_banque': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'vehicles.booking': {
            'Meta': {'object_name': 'Booking'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vehicles.Card']", 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vehicles.Location']", 'null': 'True', 'blank': 'True'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vehicles.Provider']"}),
            'reason': ('django.db.models.fields.TextField', [], {}),
            'remark': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'remark_agepoly': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'0_draft'", 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['units.Unit']"}),
            'vehicletype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vehicles.VehicleType']"})
        },
        u'vehicles.bookinglogging': {
            'Meta': {'object_name': 'BookingLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['vehicles.Booking']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'vehicles.card': {
            'Meta': {'object_name': 'Card'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vehicles.Provider']"})
        },
        u'vehicles.cardlogging': {
            'Meta': {'object_name': 'CardLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['vehicles.Card']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'vehicles.location': {
            'Meta': {'object_name': 'Location'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url_location': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'vehicles.locationlogging': {
            'Meta': {'object_name': 'LocationLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['vehicles.Location']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'vehicles.provider': {
            'Meta': {'object_name': 'Provider'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'vehicles.providerlogging': {
            'Meta': {'object_name': 'ProviderLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['vehicles.Provider']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        },
        u'vehicles.vehicletype': {
            'Meta': {'object_name': 'VehicleType'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['vehicles.Provider']"})
        },
        u'vehicles.vehicletypelogging': {
            'Meta': {'object_name': 'VehicleTypeLogging'},
            'extra_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['vehicles.VehicleType']"}),
            'what': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.TruffeUser']"})
        }
    }

    complete_apps = ['vehicles']