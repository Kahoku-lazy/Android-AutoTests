from django.contrib import admin
from django.db.models import Count

from .models import CaseDirectory, CaseFile, CaseProject, TestDefinition


@admin.register(CaseProject)
class CaseProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_by", "case_count", "created_at")
    search_fields = ("name", "created_by")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_case_count=Count("cases", distinct=True))

    @admin.display(description="用例数")
    def case_count(self, obj):
        return getattr(obj, "_case_count", 0) or 0


@admin.register(CaseDirectory)
class CaseDirectoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "parent", "sort_order", "created_at")
    list_filter = ("project",)
    search_fields = ("name",)
    ordering = ("project_id", "parent_id", "sort_order", "id")


@admin.register(CaseFile)
class CaseFileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "directory", "sort_order", "updated_at")
    list_filter = ("project",)
    search_fields = ("name",)


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "test_type",
        "business_type",
        "project",
        "file",
        "directory",
        "updated_at",
    )
    list_filter = ("test_type", "business_type")
    search_fields = ("id", "title")
