# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0003_newsletter'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterToList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('subscriptions_url', models.CharField(blank=True, max_length=255)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('subscriptions_url', models.CharField(blank=True, max_length=255)),
                ('target_name', models.CharField(blank=True, max_length=255)),
                ('target_email', models.EmailField(max_length=254)),
                ('newsletter', models.ForeignKey(to='hemres.Newsletter')),
                ('target_list', models.ForeignKey(to='hemres.MailingList')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
