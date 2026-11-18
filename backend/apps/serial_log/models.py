"""串口日志数据模型。"""

from django.db import models


class LogPort(models.Model):
    """日志端口登记与监听开关 → sl_log_ports（双轨制）。

    `origin=config`（配置行）：端口 / SKU / 波特率三列的真相源是平台配置
    （`DEVICE_LOG_SOURCES`），配置同步只刷新三列、不改开关；**无记录 = 开启**。
    `origin=custom`（自定义行）：三列真相源是本表，由超管经页面增删改，配置同步
    不创建、不改写、不删除自定义行。`enabled=False` 表示用户关掉了监听。
    写库一律经本 App 的 `api.py`。日志正文不进数据库，只落本地文件（见
    `engines/device/logfiles.py`）。
    """

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
    """日志关键词对照表 → sl_log_keywords（一行 = 关键词 × 功能点 × 范围）。

    条目真相源是本表（存量自 `device_log_keywords.json` 快照迁入，文件退役为种子档案）。
    `scope="*"` 表示通用（对所有型号生效），其余存 SKU 名（如 H6601）；某型号可用
    关键词为通用与该型号专用条目的**并集**，专用不覆盖通用。`feature_id` 是功能点
    业务编号（同一功能点可挂多个关键词），`sort_order` 保持表内登记行序。
    写库一律经本 App 的 `api.py`；日志正文不进数据库，只落本地文件。
    """

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
