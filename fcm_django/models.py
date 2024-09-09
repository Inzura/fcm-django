from __future__ import unicode_literals
import logging
from pyfcm import FCMNotification
from google.oauth2 import service_account
import json

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
        logger.error(f'FCMDeviceQuerySet : send_message : not supported : nothing has been sent')
        return None

        # if self:
        #     from .fcm import fcm_send_bulk_message
        #
        #     reg_ids = list(self.filter(active=True).values_list('registration_id', flat=True))
        #     if len(reg_ids) == 0:
        #         return [{'failure': len(self), 'success': 0}]
        #
        #     result = fcm_send_bulk_message(
        #         registration_ids=reg_ids,
        #         title=title,
        #         body=body,
        #         icon=icon,
        #         data=data,
        #         sound=sound,
        #         badge=badge,
        #         api_key=api_key,
        #         **kwargs
        #     )
        #
        #     results = result[0]['results']
        #     for (index, item) in enumerate(results):
        #         if 'error' in item:
        #             reg_id = reg_ids[index]
        #             self.filter(registration_id=reg_id).update(active=False)
        #
        #             if SETTINGS["DELETE_INACTIVE_DEVICES"]:
        #                 self.filter(registration_id=reg_id).delete()
        #     return result


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

    def send_message(self, title=None, body=None, icon=None, data=None, service_account_info=None, timeout=5, **kwargs):

        logger.info(f'Sending push message to FCMDevice {self.id}')

        if kwargs is not None and len(kwargs) > 0:
            logger.error(f'FCMDevice.send_message : has kwargs : {kwargs}')

        # https://pypi.org/project/pyfcm/
        # https://github.com/olucurious/pyfcm

        credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=['https://www.googleapis.com/auth/firebase.messaging'])
        fcm = FCMNotification(None, credentials=credentials, project_id=service_account_info['project_id'])

        # proxy_dict = {
        #     "http": "http://127.0.0.1",
        #     "https": "http://127.0.0.1",
        # }
        # fcm = FCMNotification(credentials=credentials, project_id=fcm_config['project_id'], proxy_dict=proxy_dict)

        # Your service account file can be gotten from:  https://console.firebase.google.com/u/0/project/_/settings/serviceaccounts/adminsdk
        # android_config (dict, optional): Android specific options for messages - https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#androidconfig
        # apns_config (dict, optional): Apple Push Notification Service specific options - https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#apnsconfig
        # webpush_config (dict, optional): Webpush protocol options - https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#webpushconfig
        # fcm_options (dict, optional): Platform independent options for features provided by the FCM SDKs - https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#fcmoptions

        # print(f'--------------------- {self.registration_id}')
        # print(f'--------------------- {title}')
        # print(f'--------------------- {body}')
        # print(f'--------------------- {data}')

        notification_title = None if title in ['', None] else title
        notification_body = None if body in ['', None] else body
        data_payload = {'inzura_data': json.dumps(data)} if data is not None else None
        try:
            result = fcm.notify(fcm_token=self.registration_id,
                                notification_title=notification_title,
                                notification_body=notification_body,
                                notification_image=icon,
                                data_payload=data_payload,
                                timeout=timeout)

            result['success'] = True
        except Exception as e:
            result = {'success': False, 'error': str(e)}
            devices = FCMDevice.objects.filter(registration_id=self.registration_id)
            devices.update(active=False)
            if SETTINGS["DELETE_INACTIVE_DEVICES"]:
                devices.delete()

        return result
