from django.contrib import admin
from .models import TestDefinition, TestCaseCache


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "enabled", "updated_at")
    list_filter = ("category", "enabled")
    search_fields = ("id", "title")


@admin.register(TestCaseCache)
class TestCaseCacheAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
