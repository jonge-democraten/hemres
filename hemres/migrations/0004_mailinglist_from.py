# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hemres', '0003_newslettertolist_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailinglist',
            name='from_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='mailinglist',
            name='from_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
