import logging
import threading

from django.apps import AppConfig

_log = logging.getLogger("ai_assistant.startup")


class AiAssistantConfig(AppConfig):
    name = "apps.ai_assistant"
    verbose_name = "AI 助手"

    def ready(self):
        """On startup: mark orphaned running AITask as failed.

        只在 ASGI 服务进程（Daphne / runserver）执行。管理命令（shell/migrate/test）
        绝不能触发——否则会把服务进程里正在执行的任务误判为孤儿。
        恢复逻辑在后台线程执行，等 apps 完全 ready 后再查库，避免
        "Accessing the database during app initialization" 警告。
        """
        import os
        import sys

        argv = " ".join(sys.argv)
        is_asgi_server = (
            os.environ.get("DJANGO_ASGI_SERVER") == "1" or "daphne" in argv or "runserver" in argv
        )
        if not is_asgi_server:
            return

        threading.Thread(
            target=self._run_startup_recovery,
            name="ai-assistant-startup-recovery",
            daemon=True,
        ).start()

    def _run_startup_recovery(self) -> None:
        """后台执行启动恢复：把上次进程遗留的 running 任务置为 failed。"""
        from django.apps import apps as django_apps
        from django.utils import timezone

        django_apps.ready_event.wait()

        try:
            from .models import AITask

            recovered = AITask.objects.filter(status="running").update(
                status="failed",
                result="执行中断：服务重启导致任务线程终止",
                finished_at=timezone.now(),
            )
            if recovered:
                _log.info("Startup recovery: %d orphaned running task(s) → failed", recovered)
        except Exception as e:
            _log.exception("Startup recovery failed: %s", e)
