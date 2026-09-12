from django.contrib import admin

from .models import (
    ApiEndpoint,
    ApiGroup,
    Element,
    LocatorDirectory,
    LocatorProject,
    Page,
    PageFlow,
    WebElement,
    WebGroup,
    WebPageFlow,
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
    list_display = ("id", "label", "package", "activity", "directory", "element_count", "created_at")
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


@admin.register(WebGroup)
class WebGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_folder", "sort_order", "created_at")
    search_fields = ("name",)
    list_filter = ("is_folder",)


@admin.register(WebElement)
class WebElementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "group",
        "directory",
        "locator_type",
        "locator_value",
        "is_test_point",
        "updated_at",
    )
    search_fields = ("name", "locator_value", "page_url", "tags")
    list_filter = ("locator_type", "is_test_point")


@admin.register(WebPageFlow)
class WebPageFlowAdmin(admin.ModelAdmin):
    list_display = ("id", "from_group", "to_group", "trigger_action", "created_at")


@admin.register(ApiGroup)
class ApiGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "is_folder", "sort_order", "created_at")
    search_fields = ("name",)
    list_filter = ("is_folder",)


@admin.register(ApiEndpoint)
class ApiEndpointAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "group",
        "directory",
        "method",
        "url",
        "is_test_point",
        "updated_at",
    )
    search_fields = ("name", "url", "tags")
    list_filter = ("method", "is_test_point")
