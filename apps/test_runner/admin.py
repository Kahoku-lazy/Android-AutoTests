from django.contrib import admin

from .models import TaskCard, TestResult, TestRunRecord, TestSOP


@admin.register(TestSOP)
class TestSOPAdmin(admin.ModelAdmin):
    list_display = ("id", "sop_id", "conv_id", "phase", "status", "created_at", "updated_at")
    list_filter = ("phase", "status")
    search_fields = ("sop_id", "conv_id")
    ordering = ("-updated_at",)


@admin.register(TestRunRecord)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ("id", "run_id", "status", "device_serial", "loop_count", "started_at")
    list_filter = ("status",)
    search_fields = ("run_id",)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("id", "case_display", "iteration", "result", "duration_ms", "created_at")
    list_filter = ("result",)
    search_fields = ("case_id",)

    @admin.display(description="用例 ID")
    def case_display(self, obj):
        return obj.case_id or "(已删除)"


@admin.register(TaskCard)
class TaskCardAdmin(admin.ModelAdmin):
    list_display = ("task_id", "name", "creator", "mode", "device_serial", "running", "created_at")
    list_filter = ("mode", "running")
    search_fields = ("task_id", "name", "creator")
    ordering = ("-created_at",)
