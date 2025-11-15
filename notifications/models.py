from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models


class Notification(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    channels = JSONField(default=list)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    metadata = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification #{self.pk} -> {self.user}"
Ё

class DeliveryAttempt(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    notification = models.ForeignKey(
        Notification, related_name="attempts", on_delete=models.CASCADE
    )
    channel = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices)
    details = JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.notification_id} via {self.channel} ({self.status})"
