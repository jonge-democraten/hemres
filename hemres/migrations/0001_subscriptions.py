# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import hemres.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSubscriberAccessToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=255)),
                ('janeus_groups_auto', models.TextField(default=b'', blank=True)),
                ('janeus_groups_required', models.TextField(default=b'', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=255, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JaneusSubscriber',
            fields=[
                ('subscriber_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hemres.Subscriber')),
                ('member_id', models.IntegerField(unique=True)),
                ('janeus_name', models.CharField(default=b'', max_length=255, blank=True)),
            ],
            options={
            },
            bases=('hemres.subscriber',),
        ),
        migrations.CreateModel(
            name='EmailSubscriber',
            fields=[
                ('subscriber_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hemres.Subscriber')),
                ('email', models.EmailField(unique=True, max_length=254)),
            ],
            options={
            },
            bases=('hemres.subscriber',),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='subscriptions',
            field=models.ManyToManyField(related_name=b'subscribers', to='hemres.MailingList', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='janeussubscriberaccesstoken',
            name='subscriber',
            field=models.OneToOneField(related_name=b'token', to='hemres.JaneusSubscriber'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailsubscriberaccesstoken',
            name='subscriber',
            field=models.OneToOneField(related_name=b'token', to='hemres.EmailSubscriber'),
            preserve_default=True,
        ),
    ]
