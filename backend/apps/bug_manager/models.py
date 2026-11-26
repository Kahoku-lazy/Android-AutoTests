from django.db import models


class BugTicket(models.Model):
    CATEGORY_UI_AUTOMATION = "ui_automation"
    CATEGORY_CASE_AUTHORING = "case_authoring"
    CATEGORY_REQUIREMENT_BREAKDOWN = "requirement_breakdown"
    CATEGORY_CHOICES = [
        (CATEGORY_UI_AUTOMATION, "UI 自动化"),
        (CATEGORY_CASE_AUTHORING, "测试用例编写"),
        (CATEGORY_REQUIREMENT_BREAKDOWN, "需求拆解"),
    ]

    STATUS_OPEN = "open"
    STATUS_RESOLVED = "resolved"
    STATUS_IGNORED = "ignored"
    STATUS_CHOICES = [
        (STATUS_OPEN, "待处理"),
        (STATUS_RESOLVED, "已解决"),
        (STATUS_IGNORED, "已忽略"),
    ]

    task_id = models.PositiveIntegerField(db_index=True)
    task_title = models.CharField(max_length=500, default="", blank=True)
    task_kind = models.CharField(max_length=32, default="", blank=True)
    task_status = models.CharField(max_length=20, default="", blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, db_index=True)
    source_ref = models.CharField(max_length=64, default="task")
    title = models.CharField(max_length=500)
    case_label = models.CharField(max_length=500, default="", blank=True)
    case_rows = models.JSONField(default=list, blank=True)
    detail = models.TextField(default="", blank=True)
    failure = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    agent_id = models.PositiveIntegerField(default=0, db_index=True)
    created_by = models.CharField(max_length=64, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bug_tickets"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["task_id", "category", "source_ref"],
                name="uk_bug_task_category_ref",
            ),
        ]
        indexes = [
            models.Index(fields=["category", "status"], name="idx_bug_category_status"),
            models.Index(fields=["task_id", "created_at"], name="idx_bug_task_created"),
        ]
        verbose_name = "BUG 单"
        verbose_name_plural = "BUG 单"

    def __str__(self) -> str:
        return f"{self.bug_no} {self.title}"

    @property
    def bug_no(self) -> str:
        return f"BUG-{self.id:04d}"
