"""case-manager ORM models — cm_ prefix tables."""

from django.db import models


class CaseDirectory(models.Model):
    """Two-level directory tree for organising test cases → cm_case_directories."""

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
        db_table = "cm_case_directories"
        unique_together = ("parent", "name")

    def __str__(self):
        prefix = f"{self.parent.name} / " if self.parent else ""
        return f"{prefix}{self.name}"


class TestDefinition(models.Model):
    """Executable test case definition → cm_test_definitions."""

    id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=500)
    category = models.CharField(max_length=200, default="", blank=True)
    description = models.TextField(default="", blank=True)
    steps = models.TextField(default="", blank=True)
    steps_json = models.TextField(default="[]")
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

    class Meta:
        db_table = "cm_test_definitions"

    def __str__(self):
        return self.title


class TestCaseCache(models.Model):
    """YAML export cache → cm_test_cases."""

    name = models.CharField(max_length=500)
    description = models.TextField(default="", blank=True)
    yaml_content = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cm_test_cases"

    def __str__(self):
        return self.name
