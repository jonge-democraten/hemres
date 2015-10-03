# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0007_newsletter_site'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='newsletter',
            options={},
        ),
        migrations.RemoveField(
            model_name='newsletter',
            name='owner',
        ),
    ]
