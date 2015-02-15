# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0001_subscriptions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='janeussubscriber',
            name='janeus_name',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mailinglist',
            name='janeus_groups_auto',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mailinglist',
            name='janeus_groups_required',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='name',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
