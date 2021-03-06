# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-09-24 10:50
from __future__ import unicode_literals
from django.db.models import Count

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def remove_duplicate_fcm_devices(apps, schema_editor):
    FCMDevice = apps.get_model("fcm_django", "FCMDevice")
    duplicate_devices = FCMDevice.objects.values('user__id').annotate(Count('user__id')).filter(user__id__count__gt=1)
    for devices in duplicate_devices:
        user_id = devices["user__id"]
        for device in FCMDevice.objects.filter(user__id=user_id).order_by("id")[1:]:
            device.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('fcm_django', '0004_auto_20190225_1027'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_fcm_devices),
        migrations.AlterField(
            model_name='fcmdevice',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='fcm_devices', to=settings.AUTH_USER_MODEL, unique=True),
        ),
    ]
