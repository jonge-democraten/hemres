# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import hemres.models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSubscriberAccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255)),
                ('expiration_date', models.DateTimeField(default=hemres.models.create_expiration_date)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JaneusSubscriberAccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255)),
                ('expiration_date', models.DateTimeField(default=hemres.models.create_expiration_date)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=255)),
                ('janeus_groups_auto', models.TextField(default='', blank=True)),
                ('janeus_groups_required', models.TextField(default='', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template', models.TextField()),
                ('subject', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('public', models.BooleanField(default=True)),
                ('site', models.ForeignKey(editable=False, to='sites.Site')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('template', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterToList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscriptions_url', models.CharField(max_length=255, blank=True)),
                ('sent', models.BooleanField(default=False)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('newsletter', models.ForeignKey(to='hemres.Newsletter')),
                ('target_list', models.ForeignKey(to='hemres.MailingList')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NewsletterToSubscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscriptions_url', models.CharField(max_length=255, blank=True)),
                ('target_name', models.CharField(max_length=255, blank=True)),
                ('target_email', models.EmailField(max_length=254)),
                ('newsletter', models.ForeignKey(to='hemres.Newsletter')),
                ('target_list', models.ForeignKey(to='hemres.MailingList')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, default='', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JaneusSubscriber',
            fields=[
                ('subscriber_ptr', models.OneToOneField(primary_key=True, serialize=False, to='hemres.Subscriber', auto_created=True, parent_link=True)),
                ('member_id', models.IntegerField(unique=True)),
                ('janeus_name', models.CharField(max_length=255, default='', blank=True)),
            ],
            options={
            },
            bases=('hemres.subscriber',),
        ),
        migrations.CreateModel(
            name='EmailSubscriber',
            fields=[
                ('subscriber_ptr', models.OneToOneField(primary_key=True, serialize=False, to='hemres.Subscriber', auto_created=True, parent_link=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
            ],
            options={
            },
            bases=('hemres.subscriber',),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='subscriptions',
            field=models.ManyToManyField(to='hemres.MailingList', related_name='subscribers', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='janeussubscriberaccesstoken',
            name='subscriber',
            field=models.OneToOneField(to='hemres.JaneusSubscriber', related_name='token'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailsubscriberaccesstoken',
            name='subscriber',
            field=models.OneToOneField(to='hemres.EmailSubscriber', related_name='token'),
            preserve_default=True,
        ),
    ]
