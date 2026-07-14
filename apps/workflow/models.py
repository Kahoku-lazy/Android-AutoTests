"""workflow ORM — wf_ directories / wf_documents（JSON 配置 + 唯一 doc_id）."""

from django.db import models


class WorkflowDirectory(models.Model):
    """工作流资源目录 → wf_directories."""

    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wf_directories"
        unique_together = ("parent", "name")
        verbose_name = "工作流目录"
        verbose_name_plural = "工作流目录"

    def __str__(self):
        prefix = f"{self.parent.name} / " if self.parent else ""
        return f"{prefix}{self.name}"


class WorkflowDocument(models.Model):
    """页面流 / 测试用例 JSON 文档 → wf_documents."""

    TYPE_PAGE_FLOW = "page_flow"
    TYPE_TEST_CASE = "test_case"
    TYPE_CHOICES = [
        (TYPE_PAGE_FLOW, "页面流"),
        (TYPE_TEST_CASE, "测试用例"),
    ]

    # 业务唯一 ID（导入导出与前端管理主键）
    doc_id = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    config_json = models.TextField(default="{}")
    directory = models.ForeignKey(
        WorkflowDirectory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    description = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wf_documents"
        verbose_name = "工作流文档"
        verbose_name_plural = "工作流文档"
        indexes = [
            models.Index(fields=["doc_type", "directory"]),
        ]

    def __str__(self):
        return f"[{self.doc_type}] {self.doc_id} {self.title}"
