from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    name = "backend.apps.ai_assistant"
    verbose_name = "AI 助手"

    def ready(self) -> None:
        """启动时把上次没跑完的测试对话标为已中断。测试建库阶段不写库。"""
        from django.conf import settings
        from django.db.utils import OperationalError, ProgrammingError

        if getattr(settings, "TESTING", False) or "pytest" in __import__("sys").modules:
            return
        from backend.apps.ai_assistant.services.assistant_threads import mark_interrupted_running

        try:
            mark_interrupted_running()
        except (OperationalError, ProgrammingError):
            return
