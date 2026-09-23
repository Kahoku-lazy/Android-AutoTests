from django.contrib import admin

from .models import (
    Element,
    LocatorDirectory,
    LocatorProject,
    Page,
    PageFlow,
)


@admin.register(LocatorProject)
class LocatorProjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "updated_at")
    readonly_fields = ("code", "created_at", "updated_at")


@admin.register(LocatorDirectory)
class LocatorDirectoryAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "parent", "sort_order", "updated_at")
    list_filter = ("project",)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "label",
        "package",
        "activity",
        "directory",
        "element_count",
        "created_at",
    )
    search_fields = ("label", "package")


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "page",
        "class_name",
        "text_val",
        "resource_id",
        "clickable",
        "is_test_point",
    )
    search_fields = ("text_val", "resource_id", "alias")
    list_filter = ("clickable", "is_test_point")


@admin.register(PageFlow)
class PageFlowAdmin(admin.ModelAdmin):
    list_display = ("id", "from_page", "to_page", "trigger_action", "created_at")
