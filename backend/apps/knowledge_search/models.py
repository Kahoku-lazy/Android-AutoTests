import uuid

from django.db import models


class KnowledgeModule(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=200)
    data_dir = models.CharField(max_length=500)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ks_modules"
        ordering = ["name"]
        verbose_name = "知识库模块"
        verbose_name_plural = "知识库模块"

    def __str__(self):
        return f"{self.name} [{'启用' if self.enabled else '禁用'}]"


class RetrievalSettings(models.Model):
    embedding_model_id = models.PositiveIntegerField()
    top_k = models.PositiveIntegerField(default=4)
    score_threshold = models.FloatField(default=0.45)
    chunk_size = models.PositiveIntegerField(default=400)
    chunk_overlap = models.PositiveIntegerField(default=60)
    index_epoch = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ks_retrieval_settings"
        verbose_name = "知识库检索配置"
        verbose_name_plural = "知识库检索配置"

    def __str__(self):
        return f"epoch {self.index_epoch} / top_k {self.top_k}"


class KsEvalRun(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    run_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    module_name = models.CharField(max_length=64)
    module_snapshot = models.JSONField(default=dict)
    model_config_id = models.IntegerField(null=True, blank=True)
    model_snapshot = models.JSONField(default=dict)
    pos_count = models.PositiveIntegerField(default=30)
    neg_count = models.PositiveIntegerField(default=10)
    seed = models.BigIntegerField(default=0)
    status = models.CharField(max_length=16, default=STATUS_PENDING)
    phase = models.CharField(max_length=16, default="", blank=True)
    progress_done = models.PositiveIntegerField(default=0)
    progress_total = models.PositiveIntegerField(default=0)
    metrics = models.JSONField(default=dict, blank=True)
    cost_estimate = models.JSONField(default=dict, blank=True)
    error = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ks_eval_runs"
        ordering = ["-created_at"]
        verbose_name = "知识库评测运行"
        verbose_name_plural = "知识库评测运行"

    def __str__(self):
        return f"{self.module_name} [{self.status}]"


class KsEvalQuery(models.Model):
    KIND_POSITIVE = "positive"
    KIND_NEGATIVE = "negative"

    run = models.ForeignKey(KsEvalRun, on_delete=models.CASCADE, related_name="queries")
    kind = models.CharField(max_length=10)
    question = models.TextField()
    gold_document_id = models.CharField(max_length=64, default="", blank=True)
    gold_source = models.CharField(max_length=500, default="", blank=True)
    source_chunk_index = models.IntegerField(default=0)
    source_text = models.TextField(default="", blank=True)
    hits = models.JSONField(default=list, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    is_hit = models.BooleanField(default=False)

    class Meta:
        db_table = "ks_eval_queries"
        ordering = ["id"]
        verbose_name = "知识库评测题目"
        verbose_name_plural = "知识库评测题目"

    def __str__(self):
        return f"{self.kind}: {self.question[:30]}"
