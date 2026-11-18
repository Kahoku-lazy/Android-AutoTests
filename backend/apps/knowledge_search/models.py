"""知识库检索数据模型：模块登记（平台侧真相源）与评测运行。"""

import uuid

from django.db import models


class KnowledgeModule(models.Model):
    """知识库模块登记 → ks_modules。

    一行 = 一个模块 = 一个服务器本地只读资料目录。库名即引擎向量集合名；
    资料目录只读，索引与检索仍在 engines/ae_harness/knowledge。
    写库一律经本 App 的 api.py；检索库目录 yaml 由 registry.py 从本表派生。
    """

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


class KsEvalRun(models.Model):
    """一次自动评测运行 → ks_eval_runs。

    触发时冻结模块与模型快照：运行期间模块登记或模型配置变更不影响该运行。
    指标与逐题明细见 KsEvalQuery；写库一律经本 App 的 api.py。
    """

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
    """评测集里的一道题及其检索结果 → ks_eval_queries。

    kind=positive 时 gold_document_id 为正确答案文档编号；
    kind=negative 为语料范围外的负样本，命中即误命中。
    """

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
