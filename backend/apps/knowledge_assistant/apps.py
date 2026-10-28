"""知识库助手 App 配置。"""

from django.apps import AppConfig


class KnowledgeAssistantConfig(AppConfig):
    """知识库助手模块的 App 配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.knowledge_assistant"
    verbose_name = "知识库助手"
