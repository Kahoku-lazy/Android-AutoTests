"""element-locator ORM models — el_ prefix tables."""
from django.db import models


class Page(models.Model):
    """Recorded UI page snapshot → el_pages."""
    device = models.ForeignKey(
        'device_pool.Device', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='element_locator_pages'
    )
    label = models.CharField(max_length=500, default='', blank=True, unique=True)
    package = models.CharField(max_length=500, default='', blank=True)
    activity = models.CharField(max_length=500, default='', blank=True)
    screenshot_path = models.CharField(max_length=1000, default='', blank=True)
    element_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'el_pages'
        verbose_name = '页面'
        verbose_name_plural = '页面'

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
    is_test_point = models.BooleanField(default=False)
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
