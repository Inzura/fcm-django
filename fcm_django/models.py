from __future__ import unicode_literals
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from .settings import FCM_DJANGO_SETTINGS as SETTINGS


logger = logging.getLogger("inzura")


class Device(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"), blank=True, null=True)
    active = models.BooleanField(
        verbose_name=_("Is active"), default=True,
        help_text=_("Inactive devices will not be sent notifications")
    )
    user = models.ForeignKey(
        SETTINGS["USER_MODEL"], related_name='fcm_devices',
        blank=True, null=True, on_delete=models.CASCADE,
        unique=True
    )  # As to return queryset, OneToOne will return an object

    date_created = models.DateTimeField(
        verbose_name=_("Creation date"), auto_now_add=True, null=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return (
            self.name or str(self.device_id or "") or
            "%s for %s" % (self.__class__.__name__, self.user or "unknown user")
        )


class FCMDeviceManager(models.Manager):
    def get_queryset(self):
        return FCMDeviceQuerySet(self.model)


class FCMDeviceQuerySet(models.query.QuerySet):
    def send_message(self, title=None, body=None, icon=None, data=None, sound=None, badge=None, api_key=None, **kwargs):
        if self:
            from .fcm import fcm_send_bulk_message

            reg_ids = list(self.filter(active=True).values_list('registration_id', flat=True))
            if len(reg_ids) == 0:
                return [{'failure': len(self), 'success': 0}]

            result = fcm_send_bulk_message(
                registration_ids=reg_ids,
                title=title,
                body=body,
                icon=icon,
                data=data,
                sound=sound,
                badge=badge,
                api_key=api_key,
                **kwargs
            )

            results = result[0]['results']
            for (index, item) in enumerate(results):
                if 'error' in item:
                    reg_id = reg_ids[index]
                    self.filter(registration_id=reg_id).update(active=False)

                    if SETTINGS["DELETE_INACTIVE_DEVICES"]:
                        self.filter(registration_id=reg_id).delete()
            return result


class FCMDevice(Device):
    DEVICE_TYPES = (
        (u'ios', u'ios'),
        (u'android', u'android'),
        (u'web', u'web')
    )

    device_id = models.CharField(
        verbose_name=_("Device ID"), blank=True, null=True, db_index=True,
        help_text=_("Unique device identifier"),
        max_length=150
    )
    registration_id = models.TextField(verbose_name=_("Registration token"))
    type = models.CharField(choices=DEVICE_TYPES, max_length=10)
    objects = FCMDeviceManager()

    class Meta:
        verbose_name = _("FCM device")

    def send_message(self, title=None, body=None, icon=None, data=None, sound=None, badge=None, api_key=None, **kwargs):
        from .fcm import fcm_send_message
        result = fcm_send_message(
            registration_id=self.registration_id,
            title=title,
            body=body,
            icon=icon,
            data=data,
            sound=sound,
            badge=badge,
            api_key=api_key,
            **kwargs
        )

        device = FCMDevice.objects.filter(registration_id=self.registration_id)
        if 'error' in result['results'][0]:
            logger.info(f'Error Sending FCM for device {device.id}: {result}')
            device.update(active=False)

            if SETTINGS["DELETE_INACTIVE_DEVICES"]:
                device.delete()

        return result
