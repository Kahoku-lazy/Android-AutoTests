from django.contrib import admin

from backend.apps.bug_manager.models import BugTicket


@admin.register(BugTicket)
class BugTicketAdmin(admin.ModelAdmin):
    list_display = ("bug_no", "category", "title", "task_id", "status", "created_at")
    list_filter = ("category", "status")
    search_fields = ("title", "detail", "task_title")
    readonly_fields = ("created_at", "updated_at", "resolved_at")
