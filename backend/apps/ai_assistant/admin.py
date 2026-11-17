from django.contrib import admin

from .models import AIRole


@admin.register(AIRole)
class AIRoleAdmin(admin.ModelAdmin):
    list_display = ("role_id", "name", "model_config", "created_at")
    search_fields = ("role_id", "name")
