# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0002_newsletter_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='newsletter',
            options={'permissions': (('send_to_list', 'Can send newsletter to a list (step 1)'),)},
        ),
    ]
