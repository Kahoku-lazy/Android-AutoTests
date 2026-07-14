from django.contrib import admin
from .models import WorkflowDirectory, WorkflowDocument


@admin.register(WorkflowDirectory)
class WorkflowDirectoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "sort_order", "updated_at")
    search_fields = ("name",)


@admin.register(WorkflowDocument)
class WorkflowDocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_id", "title", "doc_type", "directory", "updated_at")
    list_filter = ("doc_type",)
    search_fields = ("doc_id", "title")
    readonly_fields = ("doc_id", "created_at", "updated_at")
