"""case-manager web automation test case model → cm_web_testcases.

Web automation uses Playwright for browser-based testing.
Default columns: 编号, 标题, 优先级, 前置条件, URL, 操作步骤, 预期结果.
"""

from django.db import models


class WebTestCase(models.Model):
    """Web automation test case — Playwright-based browser testing."""

    id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=500, verbose_name="用例标题")
    case_type = models.CharField(max_length=32, default="web_automation")
    category = models.CharField(max_length=200, default="", blank=True)
    priority = models.CharField(
        max_length=4,
        choices=[("P0", "P0 — 必测"), ("P1", "P1 — 应测"), ("P2", "P2 — 可测")],
        default="P1",
        verbose_name="优先级",
    )
    url = models.TextField(default="", blank=True, verbose_name="目标 URL")
    precondition = models.TextField(default="", blank=True, verbose_name="前置条件")
    steps = models.TextField(default="", blank=True, verbose_name="操作步骤")
    expected_result = models.TextField(default="", blank=True, verbose_name="预期结果")
    custom_columns = models.JSONField(default=list, blank=True, verbose_name="自定义列")
    rows = models.JSONField(default=list, blank=True, verbose_name="表格行数据")
    directory = models.ForeignKey(
        "CaseDirectory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="web_testcases",
    )
    description = models.TextField(default="", blank=True)
    enabled = models.BooleanField(default=True)
    design_method = models.CharField(max_length=100, default="", blank=True)
    metrics = models.TextField(default="", blank=True)
    created_by = models.CharField(max_length=200, default="", blank=True)
    updated_by = models.CharField(max_length=200, default="", blank=True)
    editing_by = models.CharField(max_length=200, default="", blank=True)
    editing_since = models.DateTimeField(null=True, blank=True)
    locked = models.BooleanField(default=False)
    visibility = models.CharField(
        max_length=20, default="public",
        choices=[("public", "所有人可见"), ("hidden", "仅创建者"), ("restricted", "指定用户")],
    )
    permitted_users = models.TextField(default="[]", blank=True)
    permission = models.CharField(
        max_length=20, default="edit",
        choices=[("edit", "所有人可编辑"), ("readonly", "所有人只读"), ("restricted", "指定用户可编辑")],
    )
    permitted_editors = models.TextField(default="[]", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_web_testcases"
        verbose_name = "Web 自动化测试用例"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["directory", "title"],
                name="unique_web_directory_title",
            ),
        ]

    def __str__(self):
        return self.title
