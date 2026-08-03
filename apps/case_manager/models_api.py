"""case-manager API interface test case model → cm_api_testcases.

Table-based CRUD. Default columns: 编号, 标题, 优先级, 前置条件, 请求头, 请求体, 预期响应文本.
User can add custom columns.
"""

from django.db import models


class ApiTestCase(models.Model):
    """API interface test case — table-style editing."""

    id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=500, verbose_name="用例标题")
    case_type = models.CharField(max_length=32, default="api_testing")
    category = models.CharField(max_length=200, default="", blank=True)
    priority = models.CharField(
        max_length=4,
        choices=[("P0", "P0 — 必测"), ("P1", "P1 — 应测"), ("P2", "P2 — 可测")],
        default="P1",
        verbose_name="优先级",
    )
    precondition = models.TextField(default="", blank=True, verbose_name="前置条件")
    method = models.CharField(max_length=10, default="GET", blank=True, verbose_name="HTTP 方法")
    url = models.TextField(default="", blank=True, verbose_name="请求 URL")
    headers = models.TextField(default="", blank=True, verbose_name="请求头")
    body = models.TextField(default="", blank=True, verbose_name="请求体")
    expected_response = models.TextField(default="", blank=True, verbose_name="预期响应文本")
    # ── Structured steps (aligns with TestDefinition.steps_json) ──
    steps_json = models.TextField(default="[]", blank=True, verbose_name="结构化步骤JSON")
    expected_status = models.IntegerField(default=200, verbose_name="预期HTTP状态码")
    assertions = models.JSONField(default=list, blank=True, verbose_name="自定义断言")
    # ── Custom columns (user-defined key-value pairs) ──
    custom_columns = models.JSONField(default=list, blank=True, verbose_name="自定义列")
    rows = models.JSONField(default=list, blank=True, verbose_name="表格行数据")
    # [{key: "col_name", values: ["v1","v2",...]}]
    directory = models.ForeignKey(
        "CaseDirectory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="api_testcases",
    )
    description = models.TextField(default="", blank=True)
    enabled = models.BooleanField(default=True)
    # ── IoT PRD fields ──
    design_method = models.CharField(max_length=100, default="", blank=True)
    metrics = models.TextField(default="", blank=True)
    # ── Collaboration ──
    created_by = models.CharField(max_length=200, default="", blank=True)
    updated_by = models.CharField(max_length=200, default="", blank=True)
    editing_by = models.CharField(max_length=200, default="", blank=True)
    editing_since = models.DateTimeField(null=True, blank=True)
    locked = models.BooleanField(default=False)
    visibility = models.CharField(
        max_length=20,
        default="public",
        choices=[("public", "所有人可见"), ("hidden", "仅创建者"), ("restricted", "指定用户")],
    )
    permitted_users = models.TextField(default="[]", blank=True)
    permission = models.CharField(
        max_length=20,
        default="edit",
        choices=[
            ("edit", "所有人可编辑"),
            ("readonly", "所有人只读"),
            ("restricted", "指定用户可编辑"),
        ],
    )
    permitted_editors = models.TextField(default="[]", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_api_testcases"
        verbose_name = "API 接口测试用例"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["directory", "title"],
                name="unique_api_directory_title",
            ),
        ]

    def __str__(self):
        return self.title
