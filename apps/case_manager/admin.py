from django.contrib import admin

from .models import CaseDirectory, TestDefinition


@admin.register(CaseDirectory)
class CaseDirectoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "sort_order", "case_count", "created_at")
    list_filter = ("parent",)
    search_fields = ("name",)
    ordering = ("parent__id", "sort_order", "id")

    def case_count(self, obj):
        return obj.test_definitions.count()

    case_count.short_description = "用例数"


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "directory", "priority", "enabled", "updated_at")
    list_filter = ("category", "enabled", "priority")
    search_fields = ("id", "title")
