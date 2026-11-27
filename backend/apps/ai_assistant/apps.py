from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    name = "backend.apps.ai_assistant"
    verbose_name = "AI 助手"

    def ready(self) -> None:
        from django.conf import settings
        from django.db.utils import OperationalError, ProgrammingError

        if getattr(settings, "TESTING", False) or "pytest" in __import__("sys").modules:
            return
        from backend.apps.ai_assistant import api

        try:
            api.mark_interrupted_threads()
        except (OperationalError, ProgrammingError):
            return
