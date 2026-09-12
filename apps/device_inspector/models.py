"""device-inspector ORM models — di_ prefix tables.

v1.7 snapshot schema per PRD-03 §6:
  di_snapshots — capture 快照（dump/OCR 解析 JSON + 截图路径 + 统计）
"""

from django.db import models


class Snapshot(models.Model):
    """One-shot page capture snapshot → di_snapshots.

    method: dump | ocr（二选一，不支持同时进行）。
    dump_json / ocr_json 存解析结果；缩略图仅存相对路径，文件落盘媒体目录。
    """

    device = models.ForeignKey(
        "device_pool.Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspector_snapshots",
    )
    serial = models.CharField(max_length=100, default="", blank=True)
    method = models.CharField(max_length=10, default="dump")  # dump | ocr
    dump_json = models.JSONField(default=dict, blank=True)
    ocr_json = models.JSONField(default=dict, blank=True)
    screenshot_path = models.CharField(max_length=1000, default="", blank=True)
    package = models.CharField(max_length=500, default="", blank=True)
    activity = models.CharField(max_length=500, default="", blank=True)
    screen_w = models.IntegerField(default=0)
    screen_h = models.IntegerField(default=0)
    element_count = models.IntegerField(default=0)
    actionable_count = models.IntegerField(default=0)
    ocr_count = models.IntegerField(default=0)
    created_by = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "di_snapshots"
        verbose_name = "检查器快照"
        verbose_name_plural = "检查器快照"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["device_id"]),
        ]

    def __str__(self):
        return f"Snapshot #{self.id} {self.serial} [{self.method}]"
