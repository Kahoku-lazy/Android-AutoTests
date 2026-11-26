from django.db import models


class LogPort(models.Model):
    ORIGIN_CONFIG = "config"
    ORIGIN_CUSTOM = "custom"
    ORIGIN_CHOICES = [(ORIGIN_CONFIG, "配置"), (ORIGIN_CUSTOM, "自定义")]

    port = models.PositiveIntegerField(unique=True)
    sku = models.CharField(max_length=100, default="", blank=True)
    baud = models.PositiveIntegerField(default=0)
    origin = models.CharField(max_length=10, choices=ORIGIN_CHOICES, default=ORIGIN_CONFIG)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sl_log_ports"
        ordering = ["port"]
        verbose_name = "日志端口监听开关"
        verbose_name_plural = "日志端口监听开关"

    def __str__(self):
        return f"{self.port} [{'监听' if self.enabled else '停止'}]"


class LogKeyword(models.Model):
    SCOPE_GENERAL = "*"

    keyword = models.CharField(max_length=200)
    feature_id = models.IntegerField()
    module = models.CharField(max_length=100)
    feature = models.CharField(max_length=200)
    scope = models.CharField(max_length=100, default=SCOPE_GENERAL)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sl_log_keywords"
        ordering = ["sort_order", "id"]
        verbose_name = "日志关键词对照"
        verbose_name_plural = "日志关键词对照"
        constraints = [
            models.UniqueConstraint(
                fields=["keyword", "feature_id", "scope"],
                name="uniq_sl_kw_keyword_feature_scope",
            ),
        ]
        indexes = [models.Index(fields=["scope"], name="sl_kw_scope_idx")]

    def __str__(self):
        return f"{self.keyword} #{self.feature_id} [{self.scope}]"
