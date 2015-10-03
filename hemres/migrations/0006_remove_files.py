# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0005_newsletter_owner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsletterattachment',
            name='file',
        ),
        migrations.RemoveField(
            model_name='newsletterattachment',
            name='newsletter',
        ),
        migrations.RemoveField(
            model_name='templateattachment',
            name='file',
        ),
        migrations.RemoveField(
            model_name='templateattachment',
            name='template',
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='files',
        ),
        migrations.DeleteModel(
            name='NewsletterAttachment',
        ),
        migrations.RemoveField(
            model_name='newslettertemplate',
            name='files',
        ),
        migrations.DeleteModel(
            name='TemplateAttachment',
        ),
        migrations.DeleteModel(
            name='NewsletterFile',
        ),
    ]
