from django.contrib import admin

from .models import CaseDirectory, TestDefinition
from .models_api import ApiTestCase
from .models_storage import StorageTestCase
from .models_web import WebTestCase


@admin.register(CaseDirectory)
class CaseDirectoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "sort_order", "case_count", "created_at")
    list_filter = ("parent",)
    search_fields = ("name",)
    ordering = ("parent__id", "sort_order", "id")

    def case_count(self, obj):
        total = obj.test_definitions.count()
        total += obj.api_testcases.count() if hasattr(obj, "api_testcases") else 0
        total += obj.web_testcases.count() if hasattr(obj, "web_testcases") else 0
        total += obj.storage_testcases.count() if hasattr(obj, "storage_testcases") else 0
        return total

    case_count.short_description = "用例数"


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "directory", "priority", "enabled", "updated_at")
    list_filter = ("category", "enabled", "priority")
    search_fields = ("id", "title")


@admin.register(ApiTestCase)
class ApiTestCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "directory", "method", "priority", "enabled", "updated_at")
    list_filter = ("enabled", "priority")
    search_fields = ("id", "title")


@admin.register(WebTestCase)
class WebTestCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "directory", "priority", "enabled", "updated_at")
    list_filter = ("enabled", "priority")
    search_fields = ("id", "title")


@admin.register(StorageTestCase)
class StorageTestCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "directory", "priority", "enabled", "updated_at")
    list_filter = ("category", "enabled", "priority")
    search_fields = ("id", "title")
