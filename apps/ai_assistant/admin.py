from django.contrib import admin

from .models import AIAgent, AIConversation, AIExecutionLog, AIMessage, AITask


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "model_provider", "model_name", "status", "created_at")
    search_fields = ("name", "tags")
    list_filter = ("status", "model_provider")


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "agent", "owner", "status", "created_at")
    list_filter = ("status", "owner")
    search_fields = ("title", "owner__username")
    list_select_related = ("agent", "owner")


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "owner_username",
        "role",
        "short_content",
        "tokens",
        "created_at",
    )
    list_filter = ("role",)
    search_fields = ("content", "conversation__title", "conversation__owner__username")
    list_select_related = ("conversation__owner",)

    @admin.display(description="用户")
    def owner_username(self, obj):
        return obj.conversation.owner.username if obj.conversation.owner_id else "—"

    @admin.display(description="内容")
    def short_content(self, obj):
        return obj.content[:80] if obj.content else ""


@admin.register(AITask)
class AITaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "agent", "status", "created_at")
    list_filter = ("status",)


@admin.register(AIExecutionLog)
class AIExecutionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "level", "short_msg", "created_at")
    list_filter = ("level",)

    @admin.display(description="message")
    def short_msg(self, obj):
        return obj.message[:80]
