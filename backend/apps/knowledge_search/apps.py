"""知识库检索 App 配置。"""

from django.apps import AppConfig


class KnowledgeSearchConfig(AppConfig):
    """知识库检索模块的 App 配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.knowledge_search"
    verbose_name = "知识库检索"
