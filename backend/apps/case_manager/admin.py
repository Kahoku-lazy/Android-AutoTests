"""case-manager admin registrations."""

from django.contrib import admin

from .models import AutomationCase, CaseProject, FunctionalCase


@admin.register(CaseProject)
class CaseProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "library_kind", "created_by", "updated_at")
    list_filter = ("library_kind",)


@admin.register(AutomationCase)
class AutomationCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "priority")


@admin.register(FunctionalCase)
class FunctionalCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "priority")
