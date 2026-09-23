"""element-locator ORM models — el_ prefix tables."""

from django.db import models

PROJECT_CODE_CHOICES = [
    ("android", "Android"),
]

SYSTEM_PROJECTS = (("android", "Android"),)


class LocatorProject(models.Model):
    """System-locked locator project → el_locator_projects (exactly one row)."""

    code = models.CharField(max_length=20, unique=True, choices=PROJECT_CODE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "el_locator_projects"
        verbose_name = "定位项目"
        verbose_name_plural = "定位项目"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class LocatorDirectory(models.Model):
    """Unlimited-depth directory inside a locator project → el_locator_directories."""

    project = models.ForeignKey(
        LocatorProject,
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
        db_table = "el_locator_directories"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "parent", "name"],
                name="uq_el_directory_project_parent_name",
            ),
        ]
        verbose_name = "定位目录"
        verbose_name_plural = "定位目录"
        indexes = [
            models.Index(fields=["project", "parent", "sort_order"], name="idx_el_dir_proj_parent"),
        ]

    def __str__(self) -> str:
        prefix = f"{self.parent.name} / " if self.parent_id else ""
        return f"{prefix}{self.name}"


class Page(models.Model):
    """Recorded UI page snapshot or folder node → el_pages.

    v7.2：快照导入时页面携带截图、页面级 OCR JSON（ocr_json）与快照溯源
    （snapshot_id）；手动创建的页面两者为空。
    项目化后：工作台文件挂 directory；parent/is_folder 仅兼容旧数据。
    """

    device = models.ForeignKey(
        "device_pool.Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="element_locator_pages",
    )
    directory = models.ForeignKey(
        LocatorDirectory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pages",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    is_folder = models.BooleanField(default=False, db_index=True)
    label = models.CharField(max_length=500, default="", blank=True, db_index=True)
    package = models.CharField(max_length=500, default="", blank=True)
    activity = models.CharField(max_length=500, default="", blank=True)
    screenshot_path = models.CharField(max_length=1000, default="", blank=True)
    ocr_json = models.JSONField(default=dict, blank=True)  # 页面级 OCR 结果（v7.2）
    snapshot_id = models.IntegerField(null=True, blank=True)  # 来源检查器快照（v7.2）
    element_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "el_pages"
        verbose_name = "页面"
        verbose_name_plural = "页面"
        indexes = [
            models.Index(fields=["parent_id", "label"], name="idx_el_pages_parent_label"),
        ]

    def __str__(self):
        return self.label or f"Page #{self.id}"


class Element(models.Model):
    """UI element with XPath candidates → el_elements.

    v7.2：快照导入补全 dump 完整字段（坐标/深度/缩略图路径等），默认值向后兼容。

    rework-save-to-elements：呈现口径收敛为「缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点」。
    新增 seq（快照全量元素的坐标顺序序号）、primary_xpath / primary_stable（主定位）与
    long_clickable / checkable / focusable（补齐七项交互标志）；既有列保留，供历史数据与其它写入入口使用。
    """

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="elements")
    class_name = models.CharField(max_length=500, default="", blank=True)
    text_val = models.CharField(max_length=2000, default="", blank=True)
    content_desc = models.CharField(max_length=2000, default="", blank=True)
    resource_id = models.CharField(max_length=500, default="", blank=True)
    bounds = models.CharField(max_length=200, default="", blank=True)
    xpath_candidates = models.TextField(default="[]")
    primary_xpath = models.CharField(max_length=2000, default="", blank=True)  # 主定位表达式
    primary_stable = models.BooleanField(default=False)  # 主定位是否稳定（同页唯一匹配）
    x = models.IntegerField(default=0)  # v7.2
    y = models.IntegerField(default=0)  # v7.2
    width = models.IntegerField(default=0)  # v7.2
    height = models.IntegerField(default=0)  # v7.2
    depth = models.IntegerField(default=0)  # v7.2
    index = models.CharField(max_length=50, default="", blank=True)  # v7.2 父内序号
    seq = models.IntegerField(default=0)  # 快照全量元素的坐标顺序序号（1 基）
    clickable = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)
    scrollable = models.BooleanField(default=False)  # v7.2
    checked = models.BooleanField(default=False)  # v7.2
    long_clickable = models.BooleanField(default=False)  # 七项交互标志补齐
    checkable = models.BooleanField(default=False)  # 七项交互标志补齐
    focusable = models.BooleanField(default=False)  # 七项交互标志补齐
    thumbnail_path = models.CharField(max_length=1000, default="", blank=True)  # v7.2
    alias = models.CharField(max_length=500, default="", blank=True)
    tags = models.CharField(max_length=500, default="", blank=True)
    is_test_point = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "el_elements"
        verbose_name = "元素"
        verbose_name_plural = "元素"
        constraints = [
            # 注意：MySQL utf8mb4 下索引上限 3072 字节，
            # 原 (page, resource_id, text_val, bounds) 组合索引超限，
            # 移除 text_val（TextField 不适合做索引），由 (page, resource_id, bounds) 唯一标识
            models.UniqueConstraint(
                fields=["page", "resource_id", "bounds"],
                name="uq_el_element_page_attrs",
            ),
        ]

    def __str__(self):
        return self.alias or self.text_val or self.resource_id or f"El #{self.id}"


class PageFlow(models.Model):
    """Page navigation flow → el_page_flows."""

    from_page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="outgoing_flows")
    to_page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="incoming_flows")
    trigger_element = models.ForeignKey(
        Element, on_delete=models.SET_NULL, null=True, blank=True, related_name="triggered_flows"
    )
    trigger_action = models.CharField(max_length=50, default="click")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "el_page_flows"
        verbose_name = "页面跳转流"
        verbose_name_plural = "页面跳转流"

    def __str__(self):
        return f"Flow #{self.id}: {self.from_page} → {self.to_page}"
