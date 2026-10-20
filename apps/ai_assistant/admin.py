from django.contrib import admin

from .models import AIAgent, AITask


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "model_provider", "model_name", "status", "created_at")
    search_fields = ("name", "tags")
    list_filter = ("status", "model_provider")


@admin.register(AITask)
class AITaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "agent", "status", "created_at")
    list_filter = ("status",)
