from django.contrib import admin

from .models import WorkflowDirectory, WorkflowDocument, WorkflowPrototype


@admin.register(WorkflowPrototype)
class WorkflowPrototypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "updated_at")
    search_fields = ("name",)


@admin.register(WorkflowDirectory)
class WorkflowDirectoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "prototype", "parent", "sort_order", "updated_at")
    list_filter = ("prototype",)
    search_fields = ("name",)


@admin.register(WorkflowDocument)
class WorkflowDocumentAdmin(admin.ModelAdmin):
    list_display = ("doc_id", "title", "doc_type", "prototype", "directory", "updated_at")
    list_filter = ("doc_type", "prototype")
    search_fields = ("doc_id", "title")
    readonly_fields = ("doc_id", "created_at", "updated_at")
