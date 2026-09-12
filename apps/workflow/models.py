"""workflow ORM — wf_prototypes / wf_directories / wf_documents."""

from django.db import models


class WorkflowPrototype(models.Model):
    """页面流顶层容器（对齐用例管理的项目）→ wf_prototypes."""

    name = models.CharField(max_length=200)
    description = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wf_prototypes"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="unique_wf_prototype_name"),
        ]
        verbose_name = "页面流原型"
        verbose_name_plural = "页面流原型"

    def __str__(self) -> str:
        return self.name


class WorkflowDirectory(models.Model):
    """工作流资源目录 → wf_directories（归属某原型）."""

    prototype = models.ForeignKey(
        WorkflowPrototype,
        on_delete=models.CASCADE,
        related_name="directories",
    )
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
        constraints = [
            models.UniqueConstraint(
                fields=["prototype", "parent", "name"],
                name="unique_wf_directory_prototype_parent_name",
            ),
        ]
        verbose_name = "工作流目录"
        verbose_name_plural = "工作流目录"

    def __str__(self):
        prefix = f"{self.parent.name} / " if self.parent else ""
        return f"{prefix}{self.name}"


class WorkflowDocument(models.Model):
    """工作流 JSON 文档 → wf_documents（归属某原型）."""

    TYPE_PAGE_FLOW = "page_flow"
    TYPE_API_FLOW = "api_flow"
    TYPE_CHOICES = [
        (TYPE_PAGE_FLOW, "页面流"),
        (TYPE_API_FLOW, "接口流"),
    ]
    SUPPORTED_TYPES = frozenset({TYPE_PAGE_FLOW, TYPE_API_FLOW})

    prototype = models.ForeignKey(
        WorkflowPrototype,
        on_delete=models.CASCADE,
        related_name="documents",
    )
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
            models.Index(fields=["prototype", "doc_type", "directory"]),
        ]

    def __str__(self):
        return f"[{self.doc_type}] {self.doc_id} {self.title}"
