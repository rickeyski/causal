# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ServiceApp'
        db.create_table('main_serviceapp', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('module_name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('enable', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
        ))
        db.send_create_signal('main', ['ServiceApp'])

        # Adding model 'UserService'
        db.create_table('main_userservice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('app', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ServiceApp'])),
            ('setup', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('share', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('public', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('auth_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('auth_object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('main', ['UserService'])

        # Adding unique constraint on 'UserService', fields ['user', 'app']
        db.create_unique('main_userservice', ['user_id', 'app_id'])

        # Adding model 'BaseAuth'
        db.create_table('main_baseauth', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['BaseAuth'])

        # Adding model 'Auth'
        db.create_table('main_auth', (
            ('baseauth_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.BaseAuth'], unique=True, primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('main', ['Auth'])

        # Adding model 'RequestToken'
        db.create_table('main_requesttoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('oauth_token', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('oauth_token_secret', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('oauth_verify', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('main', ['RequestToken'])

        # Adding model 'AccessToken'
        db.create_table('main_accesstoken', (
            ('requesttoken_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.RequestToken'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('main', ['AccessToken'])

        # Adding model 'OAuth'
        db.create_table('main_oauth', (
            ('baseauth_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main.BaseAuth'], unique=True, primary_key=True)),
            ('request_token', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.RequestToken'], null=True, blank=True)),
            ('access_token', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='main_oauth_related', null=True, to=orm['main.AccessToken'])),
        ))
        db.send_create_signal('main', ['OAuth'])

        # Adding model 'UserProfile'
        db.create_table('main_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('timezone', self.gf('timezones.fields.TimeZoneField')(default='Europe/London')),
        ))
        db.send_create_signal('main', ['UserProfile'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'UserService', fields ['user', 'app']
        db.delete_unique('main_userservice', ['user_id', 'app_id'])

        # Deleting model 'ServiceApp'
        db.delete_table('main_serviceapp')

        # Deleting model 'UserService'
        db.delete_table('main_userservice')

        # Deleting model 'BaseAuth'
        db.delete_table('main_baseauth')

        # Deleting model 'Auth'
        db.delete_table('main_auth')

        # Deleting model 'RequestToken'
        db.delete_table('main_requesttoken')

        # Deleting model 'AccessToken'
        db.delete_table('main_accesstoken')

        # Deleting model 'OAuth'
        db.delete_table('main_oauth')

        # Deleting model 'UserProfile'
        db.delete_table('main_userprofile')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.accesstoken': {
            'Meta': {'object_name': 'AccessToken', '_ormbases': ['main.RequestToken']},
            'requesttoken_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.RequestToken']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.auth': {
            'Meta': {'object_name': 'Auth', '_ormbases': ['main.BaseAuth']},
            'baseauth_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.BaseAuth']", 'unique': 'True', 'primary_key': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'main.baseauth': {
            'Meta': {'object_name': 'BaseAuth'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'main.oauth': {
            'Meta': {'object_name': 'OAuth', '_ormbases': ['main.BaseAuth']},
            'access_token': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'main_oauth_related'", 'null': 'True', 'to': "orm['main.AccessToken']"}),
            'baseauth_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.BaseAuth']", 'unique': 'True', 'primary_key': 'True'}),
            'request_token': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.RequestToken']", 'null': 'True', 'blank': 'True'})
        },
        'main.requesttoken': {
            'Meta': {'object_name': 'RequestToken'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'oauth_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'oauth_token_secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'oauth_verify': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'main.serviceapp': {
            'Meta': {'object_name': 'ServiceApp'},
            'enable': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'main.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timezone': ('timezones.fields.TimeZoneField', [], {'default': "'Europe/London'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'main.userservice': {
            'Meta': {'unique_together': "(('user', 'app'),)", 'object_name': 'UserService'},
            'app': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ServiceApp']"}),
            'auth_object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'auth_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'setup': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'share': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['main']
