"""device-pool ORM models — dp_ prefix tables.

v2 schema per PRD §5:
  dp_devices       — device registry（序列号唯一 + 元信息 + 状态 + 锁定/占用 + 连接地址/时间/添加人）
  dp_device_locks  — lock audit trail（永不删除，status 追踪生命周期）
"""

from django.db import models


class Device(models.Model):
    """ADB device registry → dp_devices.

    Status life-cycle: (new) → ONLINE ⇄ BUSY → OFFLINE; disconnect removes the row.
    """

    serial = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200, default="", blank=True)
    model = models.CharField(max_length=200, default="", blank=True)
    brand = models.CharField(max_length=100, default="", blank=True)
    screen_w = models.IntegerField(default=0)
    screen_h = models.IntegerField(default=0)
    android_version = models.CharField(max_length=20, default="", blank=True)
    connection_type = models.CharField(max_length=10, default="USB")  # USB | WIFI
    connection_addr = models.CharField(max_length=200, default="", blank=True)  # 无线设备 IP:port
    status = models.CharField(max_length=20, default="ONLINE")  # ONLINE | BUSY
    # 锁定（可见性）：锁定者用户名；空 = 公开
    locked_by = models.CharField(max_length=200, default="", blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    # 进程占用：设备检查器 / 执行引擎占用
    occupied_by = models.CharField(max_length=200, default="", blank=True)
    occupied_at = models.DateTimeField(null=True, blank=True)
    # 连接时间点 / 添加人
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
    last_heartbeat = models.DateTimeField(null=True, blank=True)  # updated by heartbeat patrol

    class Meta:
        db_table = "dp_device_locks"
        verbose_name = "设备锁"
        verbose_name_plural = "设备锁"
        indexes = [
            models.Index(fields=["device", "status"]),
        ]
        constraints = [
            # 同一设备同时最多一个活跃锁（数据库级并发控制）
            models.UniqueConstraint(
                fields=["device"],
                condition=models.Q(status="active"),
                name="uq_device_active_lock",
            ),
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
