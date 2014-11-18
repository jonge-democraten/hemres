# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import hemres.utils


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0002_futurize'),
    ]

    operations = [
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('template', models.TextField()),
                ('subject', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('public', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterAttachment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('attach_to_email', models.BooleanField(default=True)),
                ('content_id', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterFile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('file', hemres.utils.HashFileField(upload_to='hemres/files/{}')),
                ('filename', models.CharField(max_length=255)),
                ('description', models.CharField(null=True, blank=True, max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterTemplate',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('title', models.CharField(max_length=255)),
                ('template', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TemplateAttachment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('attach_to_email', models.BooleanField(default=True)),
                ('content_id', models.CharField(max_length=255)),
                ('file', models.ForeignKey(to='hemres.NewsletterFile')),
                ('template', models.ForeignKey(to='hemres.NewsletterTemplate')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='newslettertemplate',
            name='files',
            field=models.ManyToManyField(through='hemres.TemplateAttachment', to='hemres.NewsletterFile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newsletterattachment',
            name='file',
            field=models.ForeignKey(to='hemres.NewsletterFile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newsletterattachment',
            name='newsletter',
            field=models.ForeignKey(to='hemres.Newsletter'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newsletter',
            name='files',
            field=models.ManyToManyField(through='hemres.NewsletterAttachment', to='hemres.NewsletterFile'),
            preserve_default=True,
        ),
    ]
