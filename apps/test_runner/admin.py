from django.contrib import admin
from .models import TestRunRecord, TestResult


@admin.register(TestRunRecord)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_id', 'status', 'device_serial', 'loop_count')
    list_filter = ('status',)
    search_fields = ('run_id',)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_id', 'iteration', 'result', 'duration_ms', 'created_at')
    list_filter = ('result',)
    search_fields = ('case_id',)
