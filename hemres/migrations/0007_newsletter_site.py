# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('hemres', '0006_remove_files'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsletter',
            name='site',
            field=models.ForeignKey(default=0, to='sites.Site', editable=False),
            preserve_default=False,
        ),
    ]
