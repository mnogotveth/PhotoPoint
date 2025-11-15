from django.contrib import admin

from .models import DeliveryAttempt, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "scheduled_at", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "subject", "body")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DeliveryAttempt)
class DeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ("notification", "channel", "status", "started_at")
    list_filter = ("channel", "status")
    readonly_fields = ("started_at", "finished_at")
