from django.db import models

LIBRARY_AUTOMATION = "automation"
LIBRARY_FUNCTIONAL = "functional"

LIBRARY_KIND_CHOICES = [
    (LIBRARY_AUTOMATION, "自动化"),
    (LIBRARY_FUNCTIONAL, "功能"),
]

SYSTEM_CHOICES = [
    ("ANDROID", "ANDROID"),
    ("WEB", "WEB"),
    ("IOS", "IOS"),
    ("API", "API"),
]

PRIORITY_CHOICES = [
    ("P0", "P0 — 必测"),
    ("P1", "P1 — 应测"),
    ("P2", "P2 — 可测"),
]

BUSINESS_TYPE_CHOICES = [
    ("appliance", "家电"),
    ("lighting", "照明"),
    ("app", "APP"),
]

CASE_ROW_LIMIT = 999


class CaseProject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(default="", blank=True)
    library_kind = models.CharField(max_length=16, choices=LIBRARY_KIND_CHOICES)
    created_by = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_case_projects"
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "name"],
                name="unique_project_owner_name",
            ),
        ]
        verbose_name = "用例项目"
        verbose_name_plural = "用例项目"

    def __str__(self) -> str:
        return self.name


class CaseRow(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    project = models.ForeignKey(CaseProject, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    priority = models.CharField(max_length=4, choices=PRIORITY_CHOICES, default="P1")
    system = models.CharField(max_length=16, choices=SYSTEM_CHOICES, default="ANDROID")
    business_type = models.CharField(max_length=16, choices=BUSINESS_TYPE_CHOICES)
    module = models.CharField(max_length=200, default="", blank=True)
    precondition = models.TextField(default="", blank=True)
    source_case_id = models.CharField(max_length=200, default="", blank=True, db_index=True)
    source_task_id = models.CharField(max_length=64, default="", blank=True, db_index=True)
    sort_order = models.IntegerField(default=0)
    created_by = models.CharField(max_length=200, default="", blank=True)
    updated_by = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AutomationCase(CaseRow):
    project = models.ForeignKey(
        CaseProject,
        on_delete=models.CASCADE,
        related_name="automation_cases",
    )

    class Meta:
        db_table = "cm_automation_cases"
        verbose_name = "自动化用例"
        verbose_name_plural = "自动化用例"
        indexes = [
            models.Index(fields=["project", "sort_order"], name="cm_auto_case_project_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class FunctionalCase(CaseRow):
    project = models.ForeignKey(
        CaseProject,
        on_delete=models.CASCADE,
        related_name="functional_cases",
    )

    class Meta:
        db_table = "cm_functional_cases"
        verbose_name = "功能用例"
        verbose_name_plural = "功能用例"
        indexes = [
            models.Index(fields=["project", "sort_order"], name="cm_func_case_project_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class StepRow(models.Model):
    sort_order = models.PositiveIntegerField(default=1)
    action = models.TextField(default="", blank=True)
    assertion = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AutomationStep(StepRow):
    case = models.ForeignKey(
        AutomationCase,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    anchor = models.JSONField(default=dict, blank=True)
    log = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cm_automation_steps"
        ordering = ["sort_order", "id"]
        verbose_name = "自动化步骤"
        verbose_name_plural = "自动化步骤"
        indexes = [
            models.Index(fields=["case", "sort_order"], name="cm_auto_step_case_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.case_id}#{self.sort_order}"


class FunctionalStep(StepRow):
    case = models.ForeignKey(
        FunctionalCase,
        on_delete=models.CASCADE,
        related_name="steps",
    )

    class Meta:
        db_table = "cm_functional_steps"
        ordering = ["sort_order", "id"]
        verbose_name = "功能步骤"
        verbose_name_plural = "功能步骤"
        indexes = [
            models.Index(fields=["case", "sort_order"], name="cm_func_step_case_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.case_id}#{self.sort_order}"


class CaseSheetView(models.Model):
    project = models.ForeignKey(
        CaseProject,
        on_delete=models.CASCADE,
        related_name="sheet_views",
    )
    user_id = models.CharField(max_length=200)
    payload = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_case_sheet_views"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user_id"],
                name="unique_case_sheet_view_owner",
            ),
        ]
        verbose_name = "用例表视图"
        verbose_name_plural = "用例表视图"

    def __str__(self) -> str:
        return f"{self.user_id}:{self.project_id}"
