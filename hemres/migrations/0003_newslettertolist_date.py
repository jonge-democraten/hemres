# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0002_newsletter_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslettertolist',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now, blank=True),
        ),
    ]
