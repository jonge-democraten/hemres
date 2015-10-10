# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletter',
            name='date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
            preserve_default=True,
        ),
    ]
