from django.conf import settings
from rest_framework import serializers

from .models import DeliveryAttempt, Notification
from .tasks import dispatch_notification


class DeliveryAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAttempt
        fields = ("id", "channel", "status", "details", "started_at", "finished_at")


class NotificationSerializer(serializers.ModelSerializer):
    attempts = DeliveryAttemptSerializer(many=True, read_only=True)
    channels = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    class Meta:
        model = Notification
        fields = (
            "id",
            "user",
            "subject",
            "body",
            "channels",
            "status",
            "metadata",
            "scheduled_at",
            "created_at",
            "updated_at",
            "attempts",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at", "attempts", "user")

    def create(self, validated_data):
        request = self.context["request"]
        channels = validated_data.pop("channels", None) or settings.NOTIFICATION_CHANNEL_PRIORITY
        notification = Notification.objects.create(
            user=request.user, channels=channels, **validated_data
        )
        dispatch_notification.delay(notification.pk)
        return notification
