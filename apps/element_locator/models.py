"""element-locator ORM models — el_ prefix tables."""
from django.db import models


class Page(models.Model):
    """Recorded UI page snapshot or folder node → el_pages."""
    device = models.ForeignKey(
        'device_pool.Device', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='element_locator_pages'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children',
    )
    is_folder = models.BooleanField(default=False, db_index=True)
    label = models.CharField(max_length=500, default='', blank=True, db_index=True)
    package = models.CharField(max_length=500, default='', blank=True)
    activity = models.CharField(max_length=500, default='', blank=True)
    screenshot_path = models.CharField(max_length=1000, default='', blank=True)
    element_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'el_pages'
        verbose_name = '页面'
        verbose_name_plural = '页面'
        indexes = [
            models.Index(fields=['parent_id', 'label'], name='idx_el_pages_parent_label'),
        ]

    def __str__(self):
        return self.label or f"Page #{self.id}"


class Element(models.Model):
    """UI element with XPath candidates → el_elements."""
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name='elements'
    )
    class_name = models.CharField(max_length=500, default='', blank=True)
    text_val = models.CharField(max_length=2000, default='', blank=True)
    content_desc = models.CharField(max_length=2000, default='', blank=True)
    resource_id = models.CharField(max_length=500, default='', blank=True)
    bounds = models.CharField(max_length=200, default='', blank=True)
    xpath_candidates = models.TextField(default='[]')
    clickable = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)
    alias = models.CharField(max_length=500, default='', blank=True)
    tags = models.CharField(max_length=500, default='', blank=True)
    is_test_point = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'el_elements'
        verbose_name = '元素'
        verbose_name_plural = '元素'
        constraints = [
            # 注意：MySQL utf8mb4 下索引上限 3072 字节，
            # 原 (page, resource_id, text_val, bounds) 组合索引超限，
            # 移除 text_val（TextField 不适合做索引），由 (page, resource_id, bounds) 唯一标识
            models.UniqueConstraint(
                fields=['page', 'resource_id', 'bounds'],
                name='uq_el_element_page_attrs',
            ),
        ]

    def __str__(self):
        return self.alias or self.text_val or self.resource_id or f"El #{self.id}"


class PageFlow(models.Model):
    """Page navigation flow → el_page_flows."""
    from_page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name='outgoing_flows'
    )
    to_page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name='incoming_flows'
    )
    trigger_element = models.ForeignKey(
        Element, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='triggered_flows'
    )
    trigger_action = models.CharField(max_length=50, default='click')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'el_page_flows'
        verbose_name = '页面跳转流'
        verbose_name_plural = '页面跳转流'

    def __str__(self):
        return f"Flow #{self.id}: {self.from_page} → {self.to_page}"


class WebGroup(models.Model):
    """Grouping tree for web elements (project → module → page) → el_web_groups."""
    name = models.CharField(max_length=500, verbose_name="分组名称")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="children",
    )
    is_folder = models.BooleanField(default=False, db_index=True, verbose_name="仅作目录")
    sort_order = models.IntegerField(default=0, verbose_name="排序权重")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "el_web_groups"
        verbose_name = "Web 分组"
        verbose_name_plural = "Web 分组"

    def __str__(self):
        return self.name or f"WebGroup #{self.id}"


class WebElement(models.Model):
    """Manually managed web page element with multiple locator strategies → el_web_elements."""
    group = models.ForeignKey(
        WebGroup, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="elements", verbose_name="所属分组",
    )
    name = models.CharField(max_length=500, verbose_name="元素名称")
    locator_type = models.CharField(
        max_length=50,
        choices=[
            ("css_selector", "CSS Selector"),
            ("xpath", "XPath"),
            ("id", "ID"),
            ("class_name", "Class Name"),
            ("name", "Name"),
            ("tag_name", "Tag Name"),
            ("link_text", "Link Text"),
            ("partial_link_text", "Partial Link Text"),
            ("text", "Text Content"),
            ("test_id", "Test ID (data-testid)"),
            ("role", "ARIA Role"),
            ("placeholder", "Placeholder"),
        ],
        default="css_selector",
        verbose_name="定位方式",
    )
    locator_value = models.TextField(default="", verbose_name="定位表达式")
    page_url = models.TextField(default="", blank=True, verbose_name="页面 URL")
    description = models.TextField(default="", blank=True, verbose_name="元素描述")
    tags = models.CharField(max_length=500, default="", blank=True, verbose_name="标签")
    is_test_point = models.BooleanField(default=False, db_index=True, verbose_name="测试点")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "el_web_elements"
        verbose_name = "Web 元素"
        verbose_name_plural = "Web 元素"

    def __str__(self):
        return self.name or f"WebEl #{self.id}"


class ApiGroup(models.Model):
    """Grouping tree for API endpoints (project → module → endpoint) → el_api_groups."""
    name = models.CharField(max_length=500, verbose_name="分组名称")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="children",
    )
    is_folder = models.BooleanField(default=False, db_index=True, verbose_name="仅作目录")
    sort_order = models.IntegerField(default=0, verbose_name="排序权重")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "el_api_groups"
        verbose_name = "API 分组"
        verbose_name_plural = "API 分组"

    def __str__(self):
        return self.name or f"ApiGroup #{self.id}"


class ApiEndpoint(models.Model):
    """Manually managed API endpoint definition → el_api_endpoints."""
    group = models.ForeignKey(
        ApiGroup, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="endpoints", verbose_name="所属分组",
    )
    name = models.CharField(max_length=500, verbose_name="接口名称")
    method = models.CharField(
        max_length=10, default="GET",
        choices=[("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("DELETE", "DELETE"), ("PATCH", "PATCH")],
        verbose_name="请求方法",
    )
    url = models.TextField(default="", verbose_name="接口 URL")
    headers = models.JSONField(default=dict, blank=True, verbose_name="请求头")
    request_body_schema = models.JSONField(default=dict, blank=True, verbose_name="请求体结构")
    response_body_schema = models.JSONField(default=dict, blank=True, verbose_name="响应体结构")
    description = models.TextField(default="", blank=True, verbose_name="描述")
    tags = models.CharField(max_length=500, default="", blank=True, verbose_name="标签")
    is_test_point = models.BooleanField(default=False, db_index=True, verbose_name="测试点")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "el_api_endpoints"
        verbose_name = "API 接口"
        verbose_name_plural = "API 接口"

    def __str__(self):
        return f"{self.method} {self.name}"


class WebPageFlow(models.Model):
    """Web page navigation flow — from_group → to_group via trigger_element → el_web_page_flows."""
    from_group = models.ForeignKey(
        WebGroup, on_delete=models.CASCADE, related_name='outgoing_flows'
    )
    to_group = models.ForeignKey(
        WebGroup, on_delete=models.CASCADE, related_name='incoming_flows'
    )
    trigger_element = models.ForeignKey(
        WebElement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='triggered_web_flows'
    )
    trigger_action = models.CharField(max_length=50, default='click')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'el_web_page_flows'
        verbose_name = 'Web 页面跳转流'
        verbose_name_plural = 'Web 页面跳转流'

    def __str__(self):
        return f"WebFlow #{self.id}: {self.from_group} → {self.to_group}"
