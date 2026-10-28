"""模型用量明细表 — 每次模型调用一条可追溯记录。"""

import uuid

from django.db import models


class ModelUsage(models.Model):
    """一次模型调用的 token、费用与关联 ID。"""

    usage_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 事件流定位；唯一，用于重试幂等
    event_id = models.CharField(max_length=180, unique=True)
    execution_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    source = models.CharField(max_length=32, default="")
    provider = models.CharField(max_length=16, db_index=True)
    category = models.CharField(max_length=16, db_index=True)
    model = models.CharField(max_length=80)
    occurred_at = models.DateTimeField(db_index=True)
    input_tokens = models.BigIntegerField(default=0)
    output_tokens = models.BigIntegerField(default=0)
    cache_input_tokens = models.BigIntegerField(default=0)
    cache_creation_tokens = models.BigIntegerField(default=0)
    total_tokens = models.BigIntegerField(default=0)
    characters = models.BigIntegerField(default=0)
    cost_input = models.DecimalField(max_digits=16, decimal_places=8, default=0)
    cost_cache = models.DecimalField(max_digits=16, decimal_places=8, default=0)
    cost_output = models.DecimalField(max_digits=16, decimal_places=8, default=0)
    cost_total = models.DecimalField(max_digits=16, decimal_places=8, default=0)
    currency = models.CharField(max_length=8, default="CNY")
    pricing_status = models.CharField(max_length=16, default="priced")
    pricing_snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_usage_records"
        indexes = [
            models.Index(fields=["occurred_at"], name="idx_usage_time"),
            models.Index(fields=["provider", "model", "occurred_at"], name="idx_usage_model_time"),
            models.Index(fields=["category", "occurred_at"], name="idx_usage_category"),
            models.Index(fields=["source", "occurred_at"], name="idx_usage_source"),
        ]
        verbose_name = "模型用量"
        verbose_name_plural = "模型用量"

    def __str__(self):
        return f"{self.occurred_at} {self.provider}/{self.model} {self.total_tokens}"
