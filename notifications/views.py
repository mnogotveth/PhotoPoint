from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer
from .tasks import dispatch_notification


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        notification = self.get_object()
        notification.status = Notification.Status.PENDING
        notification.save(update_fields=["status", "updated_at"])
        dispatch_notification.delay(notification.pk)
        return Response({"status": "queued"})
