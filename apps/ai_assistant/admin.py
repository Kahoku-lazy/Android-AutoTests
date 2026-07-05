from django.contrib import admin
from .models import AIAgent, AITool, AIConversation, AIMessage, AITask, AIExecutionLog

@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'model_provider', 'model_name', 'status', 'created_at')
    search_fields = ('name', 'tags')
    list_filter = ('status', 'model_provider')

@admin.register(AITool)
class AIToolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'tool_type', 'agent', 'enabled')
    list_filter = ('tool_type', 'enabled')

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'agent', 'status', 'created_at')

@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'tokens', 'created_at')

@admin.register(AITask)
class AITaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'agent', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(AIExecutionLog)
class AIExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'level', 'short_msg', 'created_at')
    list_filter = ('level',)
    def short_msg(self, obj): return obj.message[:80]
    short_msg.short_description = 'message'
