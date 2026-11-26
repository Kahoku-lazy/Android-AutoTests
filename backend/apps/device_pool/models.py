from django.db import models


class Device(models.Model):
    serial = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200, default="", blank=True)
    model = models.CharField(max_length=200, default="", blank=True)
    brand = models.CharField(max_length=100, default="", blank=True)
    screen_w = models.IntegerField(default=0)
    screen_h = models.IntegerField(default=0)
    android_version = models.CharField(max_length=20, default="", blank=True)
    connection_type = models.CharField(max_length=10, default="USB")
    connection_addr = models.CharField(max_length=200, default="", blank=True)
    status = models.CharField(max_length=20, default="ONLINE")
    locked_by = models.CharField(max_length=200, default="", blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    occupied_by = models.CharField(max_length=200, default="", blank=True)
    occupied_at = models.DateTimeField(null=True, blank=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    added_by = models.CharField(max_length=200, default="", blank=True)

    @property
    def is_occupied(self):
        return bool(self.occupied_by)

    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dp_devices"
        verbose_name = "设备"
        verbose_name_plural = "设备"
        indexes = [
            models.Index(
                fields=["status"],
                name="dp_devices_status_47e1d0_idx",
            ),
        ]

    def __str__(self):
        return f"{self.name or self.model} ({self.serial})"


class DeviceLock(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="locks")
    user_id = models.CharField(max_length=200)
    lock_type = models.CharField(max_length=20, default="user")
    status = models.CharField(max_length=20, default="active")
    locked_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    timeout_seconds = models.IntegerField(default=300)
    release_reason = models.CharField(max_length=20, default="", blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "dp_device_locks"
        verbose_name = "设备锁"
        verbose_name_plural = "设备锁"
        indexes = [
            models.Index(
                fields=["device", "status"],
                name="dp_device_l_device__4b3c95_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device"],
                condition=models.Q(status="active"),
                name="uq_device_active_lock",
            ),
        ]

    @property
    def remaining_seconds(self):
        from datetime import datetime

        if self.status != "active":
            return 0
        elapsed = (datetime.now() - self.locked_at).total_seconds()
        return max(0, self.timeout_seconds - int(elapsed))

    @property
    def is_expired(self):
        return self.remaining_seconds <= 0

    def __str__(self):
        return f"Lock: {self.device.serial} by {self.user_id} [{self.status}]"
