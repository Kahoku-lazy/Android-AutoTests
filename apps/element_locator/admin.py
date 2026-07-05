from django.contrib import admin
from .models import Page, Element, PageFlow


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'package', 'activity', 'element_count', 'created_at')
    search_fields = ('label', 'package')


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'page', 'class_name', 'text_val', 'resource_id', 'clickable', 'is_test_point')
    search_fields = ('text_val', 'resource_id', 'alias')
    list_filter = ('clickable', 'is_test_point')


@admin.register(PageFlow)
class PageFlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_page', 'to_page', 'trigger_action', 'created_at')
