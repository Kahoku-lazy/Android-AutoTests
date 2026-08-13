from django.contrib import admin
from django.db.models import Count

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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _td_count=Count("test_definitions", distinct=True),
                _api_count=Count("api_testcases", distinct=True),
                _web_count=Count("web_testcases", distinct=True),
                _stor_count=Count("storage_testcases", distinct=True),
            )
        )

    @admin.display(description="用例数")
    def case_count(self, obj):
        return (
            (getattr(obj, "_td_count", 0) or 0)
            + (getattr(obj, "_api_count", 0) or 0)
            + (getattr(obj, "_web_count", 0) or 0)
            + (getattr(obj, "_stor_count", 0) or 0)
        )


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "directory", "priority", "enabled", "updated_at")
    list_filter = ("category", "enabled", "priority")
    search_fields = ("id", "title")


@admin.register(ApiTestCase)
class ApiTestCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "directory", "priority", "enabled", "updated_at")
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
