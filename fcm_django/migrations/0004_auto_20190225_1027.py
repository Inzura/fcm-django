# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-02-25 10:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fcm_django', '0003_auto_20170313_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fcmdevice',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fcm_devices', to=settings.AUTH_USER_MODEL),
        ),
    ]
