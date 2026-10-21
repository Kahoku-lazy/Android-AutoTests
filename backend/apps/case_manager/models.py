"""case-manager ORM models — cm_ prefix tables (document cases + projects)."""

from django.db import models

SYSTEM_CHOICES = [
    ("ANDROID", "ANDROID"),
    ("WEB", "WEB"),
    ("IOS", "IOS"),
    ("API", "API"),
]

CASE_TYPE_CHOICES = [
    ("FUNC", "功能"),
    ("AUTO", "自动化"),
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


class CaseProject(models.Model):
    """Test-case project container → cm_case_projects."""

    name = models.CharField(max_length=200)
    description = models.TextField(default="", blank=True)
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


class CaseDirectory(models.Model):
    """Unlimited-depth directory tree inside a project → cm_case_directories."""

    project = models.ForeignKey(
        CaseProject,
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
    created_by = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_case_directories"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "parent", "name"],
                name="unique_directory_project_parent_name",
            ),
        ]
        verbose_name = "用例目录"
        verbose_name_plural = "用例目录"

    def __str__(self) -> str:
        prefix = f"{self.parent.name} / " if self.parent_id else ""
        return f"{prefix}{self.name}"


class CaseFile(models.Model):
    """Case sheet (tree leaf file) → cm_case_files. Rows live in TestDefinition."""

    project = models.ForeignKey(
        CaseProject,
        on_delete=models.CASCADE,
        related_name="files",
    )
    directory = models.ForeignKey(
        CaseDirectory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="files",
    )
    name = models.CharField(max_length=200)
    sort_order = models.IntegerField(default=0)
    created_by = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_case_files"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "directory", "name"],
                name="unique_file_project_directory_name",
            ),
        ]
        verbose_name = "用例文件"
        verbose_name_plural = "用例文件"
        indexes = [
            models.Index(
                fields=["project", "directory", "sort_order"],
                name="cm_case_fil_project_9a1b2c_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class TestDefinition(models.Model):
    """Document-style test case row → cm_test_definitions."""

    id = models.CharField(max_length=200, primary_key=True)
    project = models.ForeignKey(
        CaseProject,
        on_delete=models.CASCADE,
        related_name="cases",
    )
    file = models.ForeignKey(
        CaseFile,
        on_delete=models.CASCADE,
        related_name="cases",
    )
    directory = models.ForeignKey(
        CaseDirectory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cases",
    )
    title = models.CharField(max_length=500)
    priority = models.CharField(max_length=4, choices=PRIORITY_CHOICES, default="P1")
    system = models.CharField(max_length=16, choices=SYSTEM_CHOICES, default="ANDROID")
    case_type = models.CharField(max_length=8, choices=CASE_TYPE_CHOICES, default="AUTO")
    business_type = models.CharField(max_length=16, choices=BUSINESS_TYPE_CHOICES)
    module = models.CharField(max_length=200, default="", blank=True)
    precondition = models.TextField(default="", blank=True)
    sort_order = models.IntegerField(default=0)
    created_by = models.CharField(max_length=200, default="", blank=True)
    updated_by = models.CharField(max_length=200, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_test_definitions"
        verbose_name = "用例定义"
        verbose_name_plural = "用例定义"
        indexes = [
            models.Index(
                fields=["project", "file", "sort_order"],
                name="cm_test_def_project_file_idx",
            ),
            models.Index(
                fields=["project", "directory", "sort_order"],
                name="cm_test_def_project_032175_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class CaseStep(models.Model):
    """Ordered step of a document case → cm_case_steps.

    步骤顺序即执行顺序：``sort_order`` 由服务端按提交顺序重编号，客户端不指定。
    """

    case = models.ForeignKey(
        TestDefinition,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    sort_order = models.PositiveIntegerField(default=1)
    action = models.TextField(default="", blank=True)
    assertion = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cm_case_steps"
        ordering = ["sort_order", "id"]
        verbose_name = "用例步骤"
        verbose_name_plural = "用例步骤"
        indexes = [
            models.Index(
                fields=["case", "sort_order"],
                name="cm_case_step_case_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.case_id}#{self.sort_order}"
