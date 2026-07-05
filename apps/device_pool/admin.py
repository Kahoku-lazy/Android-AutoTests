from django.contrib import admin
from .models import Device, DeviceLock, DeviceQueue


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "serial",
        "name",
        "model",
        "brand",
        "status",
        "connection_type",
        "locked_by",
        "last_seen",
        "created_at",
    )
    search_fields = ("serial", "name", "model", "brand")
    list_filter = ("status", "connection_type")
    readonly_fields = ("created_at", "last_seen")


@admin.register(DeviceLock)
class DeviceLockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "device",
        "user_id",
        "status",
        "locked_at",
        "released_at",
        "timeout_seconds",
        "release_reason",
    )
    search_fields = ("user_id", "device__serial")
    list_filter = ("status", "release_reason")
    readonly_fields = ("locked_at",)


@admin.register(DeviceQueue)
class DeviceQueueAdmin(admin.ModelAdmin):
    list_display = ("id", "device", "user_id", "status", "requested_at", "assigned_at")
    search_fields = ("user_id", "device__serial")
    list_filter = ("status",)
    readonly_fields = ("requested_at",)
