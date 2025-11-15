import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import DeliveryAttempt, Notification

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    success: bool
    details: Dict = None


class BaseChannel:
    name = "base"

    def send(self, notification: Notification) -> DeliveryResult:
        raise NotImplementedError


class EmailChannel(BaseChannel):
    name = "email"

    def send(self, notification: Notification) -> DeliveryResult:
        try:
            send_mail(
                subject=notification.subject or "Notification",
                message=notification.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False,
            )
            return DeliveryResult(True, {"provider": "django-email"})
        except Exception as exc:
            logger.exception("Email send failed", exc_info=exc)
            return DeliveryResult(False, {"error": str(exc)})


class SmsChannel(BaseChannel):
    name = "sms"

    def send(self, notification: Notification) -> DeliveryResult:
        if not settings.SMS_PROVIDER_URL or not settings.SMS_PROVIDER_TOKEN:
            return DeliveryResult(False, {"error": "SMS provider not configured"})

        payload = {
            "to": notification.metadata.get("phone") or notification.user.username,
            "text": notification.body,
        }
        headers = {"Authorization": f"Bearer {settings.SMS_PROVIDER_TOKEN}"}

        try:
            response = requests.post(
                settings.SMS_PROVIDER_URL, json=payload, headers=headers, timeout=5
            )
            response.raise_for_status()
            return DeliveryResult(True, {"provider": "sms-gateway", "response": response.json()})
        except Exception as exc:
            logger.exception("SMS send failed", exc_info=exc)
            return DeliveryResult(False, {"error": str(exc)})


class TelegramChannel(BaseChannel):
    name = "telegram"

    def send(self, notification: Notification) -> DeliveryResult:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = notification.metadata.get("telegram_chat_id")

        if not token or not chat_id:
            return DeliveryResult(
                False, {"error": "Telegram token or chat_id missing"}
            )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": notification.body}

        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            return DeliveryResult(True, {"provider": "telegram", "response": response.json()})
        except Exception as exc:
            logger.exception("Telegram send failed", exc_info=exc)
            return DeliveryResult(False, {"error": str(exc)})


class NotificationDispatcher:
    channel_map = {
        EmailChannel.name: EmailChannel,
        SmsChannel.name: SmsChannel,
        TelegramChannel.name: TelegramChannel,
    }

    def __init__(
        self, notification: Notification, channels: Optional[Iterable[str]] = None
    ):
        self.notification = notification
        priority = channels or notification.channels or settings.NOTIFICATION_CHANNEL_PRIORITY
        self.adapters: List[BaseChannel] = [
            self.channel_map[name]() for name in priority if name in self.channel_map
        ]

    def dispatch(self) -> bool:
        if not self.adapters:
            logger.warning("No channels defined for notification %s", self.notification.pk)
            self.notification.status = Notification.Status.FAILED
            self.notification.save(update_fields=["status", "updated_at"])
            return False

        with transaction.atomic():
            locked = Notification.objects.select_for_update().get(pk=self.notification.pk)
            locked.status = Notification.Status.IN_PROGRESS
            locked.save(update_fields=["status", "updated_at"])
            self.notification.refresh_from_db()

        for adapter in self.adapters:
            result = adapter.send(self.notification)
            DeliveryAttempt.objects.create(
                notification=self.notification,
                channel=adapter.name,
                status=DeliveryAttempt.Status.SUCCESS if result.success else DeliveryAttempt.Status.FAILED,
                details=result.details or {},
            )
            if result.success:
                self.notification.status = Notification.Status.SENT
                self.notification.save(update_fields=["status", "updated_at"])
                return True

        self.notification.status = Notification.Status.FAILED
        self.notification.save(update_fields=["status", "updated_at"])
        return False
