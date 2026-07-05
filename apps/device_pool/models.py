"""device-pool ORM models — dp_ prefix tables.

v2 schema per PRD §5:
  dp_devices       — 13 fields: device registry with full metadata
  dp_device_locks  —  7 fields: lock audit trail (never deleted)
  dp_device_queue  —  6 fields: FIFO waiting queue
"""

from django.db import models


class Device(models.Model):
    """ADB device registry → dp_devices.

    Status life-cycle: (new) → ONLINE ⇄ BUSY → OFFLINE / DISCONNECTED → ONLINE.
    """

    serial = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200, default="", blank=True)
    model = models.CharField(max_length=200, default="", blank=True)
    brand = models.CharField(max_length=100, default="", blank=True)
    screen_w = models.IntegerField(default=0)
    screen_h = models.IntegerField(default=0)
    android_version = models.CharField(max_length=20, default="", blank=True)
    connection_type = models.CharField(max_length=10, default="USB")  # USB | WIFI
    status = models.CharField(
        max_length=20, default="ONLINE"
    )  # ONLINE | BUSY | OFFLINE | DISCONNECTED
    # User binding: which login user exclusively owns this device
    locked_by = models.CharField(max_length=200, default="", blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    # Process occupation: which process is currently using the hardware
    occupied_by = models.CharField(max_length=200, default="", blank=True)
    occupied_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_occupied(self):
        return bool(self.occupied_by)

    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dp_devices"
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name or self.model} ({self.serial})"


class DeviceLock(models.Model):
    """Device lock audit record → dp_device_locks.

    Locks are never deleted; status tracks the life-cycle:
      active → released (manual / timeout / disconnect / force)
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="locks")
    user_id = models.CharField(max_length=200)
    lock_type = models.CharField(max_length=20, default="user")  # user | process
    status = models.CharField(max_length=20, default="active")  # active | released | expired
    locked_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    timeout_seconds = models.IntegerField(default=300)
    release_reason = models.CharField(
        max_length=20, default="", blank=True
    )  # manual | timeout | disconnect | force

    class Meta:
        db_table = "dp_device_locks"
        indexes = [
            models.Index(fields=["device", "status"]),
        ]

    @property
    def remaining_seconds(self):
        """Seconds until this lock expires (0 if already expired)."""
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


class DeviceQueue(models.Model):
    """FIFO waiting queue → dp_device_queue (v2).

    When a device is BUSY and another user wants it, they join the queue.
    On release the first waiting entry is auto-assigned.
    """

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="queue_entries")
    user_id = models.CharField(max_length=200)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, default="waiting"
    )  # waiting | assigned | cancelled | timeout
    assigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "dp_device_queue"
        ordering = ["requested_at"]

    def __str__(self):
        return f"Queue: {self.user_id} → {self.device.serial} [{self.status}]"
