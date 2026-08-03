"""case-manager ORM models — cm_ prefix tables."""

from django.db import models


class CaseDirectory(models.Model):
    """Two-level directory tree for organising test cases → cm_case_directories."""

    name = models.CharField(max_length=200)
    case_type = models.CharField(
        max_length=32,
        default="ui_automation",
        help_text="ui_automation / storage / api_testing — each module has independent tree",
    )
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
    # ── 权限控制 ──
    created_by = models.CharField(max_length=200, default="", blank=True)
    allow_create = models.BooleanField(default=True)
    allow_delete = models.BooleanField(default=False)

    class Meta:
        db_table = "cm_case_directories"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name", "case_type"],
                name="unique_directory_parent_name_type",
            ),
        ]
        verbose_name = "用例目录"
        verbose_name_plural = "用例目录"

    def __str__(self):
        prefix = f"{self.parent.name} / " if self.parent else ""
        return f"{prefix}{self.name}"


class TestDefinition(models.Model):
    """Executable test case definition → cm_test_definitions."""

    id = models.CharField(max_length=200, primary_key=True)
    case_type = models.CharField(
        max_length=32,
        default="ui_automation",
        help_text="ui_automation / storage / api_testing",
    )
    title = models.CharField(max_length=500)
    category = models.CharField(max_length=200, default="", blank=True)
    description = models.TextField(default="", blank=True)
    steps = models.TextField(default="", blank=True)
    steps_json = models.TextField(default="[]")
    watchers = models.JSONField(default=list, blank=True)  # [{xpath, action}] popup handling
    enabled = models.BooleanField(default=True)
    package_name = models.CharField(max_length=200, default="", blank=True)
    # ── IoT PRD → test-case fields (from iot-test-case-agent) ──
    priority = models.CharField(
        max_length=4,
        choices=[("P0", "P0 — 必测"), ("P1", "P1 — 应测"), ("P2", "P2 — 可测")],
        default="P1",
    )
    design_method = models.CharField(
        max_length=100,
        default="",
        blank=True,
        help_text="五法之一：场景流法 / 等价类边界值 / 判定表 / 正交排列 / 错误推测",
    )
    precondition = models.TextField(default="", blank=True)
    expected_result = models.TextField(default="", blank=True)
    metrics = models.TextField(default="", blank=True, help_text="量化指标")
    directory = models.ForeignKey(
        CaseDirectory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_definitions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # ── 协作追踪 ──
    created_by = models.CharField(max_length=200, default="", blank=True)
    updated_by = models.CharField(max_length=200, default="", blank=True)
    # ── 编辑锁 ──
    editing_by = models.CharField(max_length=200, default="", blank=True)
    editing_since = models.DateTimeField(null=True, blank=True)
    # ── 持久锁（创建者控制）──
    locked = models.BooleanField(default=False)
    # ── 可见性控制 ──
    visibility = models.CharField(
        max_length=20,
        default="public",
        choices=[("public", "所有人可见"), ("hidden", "仅创建者"), ("restricted", "指定用户")],
    )
    permitted_users = models.TextField(default="[]", blank=True)  # JSON: ["user1","user2"]
    # ── 编辑权限 ──
    permission = models.CharField(
        max_length=20,
        default="edit",
        choices=[
            ("edit", "所有人可编辑"),
            ("readonly", "所有人只读"),
            ("restricted", "指定用户可编辑"),
        ],
    )
    permitted_editors = models.TextField(default="[]", blank=True)  # JSON: ["user1","user2"]

    class Meta:
        db_table = "cm_test_definitions"
        verbose_name = "用例定义"
        verbose_name_plural = "用例定义"
        constraints = [
            models.UniqueConstraint(
                fields=["directory", "title"],
                name="unique_directory_title",
            ),
        ]

    def __str__(self):
        return self.title


# Re-export for backward-compatible imports
from .models_api import ApiTestCase  # noqa: E402, F401
from .models_storage import StorageTestCase  # noqa: E402, F401
from .models_web import WebTestCase  # noqa: E402, F401
