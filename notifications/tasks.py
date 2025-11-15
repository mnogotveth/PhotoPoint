from celery import shared_task
from django.utils import timezone

from .models import Notification
from .services import NotificationDispatcher


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def dispatch_notification(self, notification_id: int):
    notification = Notification.objects.get(pk=notification_id)
    if notification.scheduled_at and notification.scheduled_at > timezone.now():
        self.retry(countdown=30)

    dispatcher = NotificationDispatcher(notification)
    dispatcher.dispatch()
