import threading

from django.apps import AppConfig

from utils.logs import backend_log


class TaskListConfig(AppConfig):
    name = "backend.apps.task_list"
    verbose_name = "任务清单"

    def ready(self):
        """On startup: mark orphaned running tasks as failed.

        Only in the ASGI server process (Daphne / runserver); management commands
        must never trigger it.
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
            name="task-list-startup-recovery",
            daemon=True,
        ).start()

    def _run_startup_recovery(self) -> None:
        from django.apps import apps as django_apps

        django_apps.ready_event.wait()

        try:
            from . import api

            recovered = api.recover_orphaned_tasks()
            if recovered:
                backend_log.info(
                    "Startup recovery: %d orphaned running task(s) → failed", recovered
                )
        except Exception as e:
            backend_log.exception("Startup recovery failed: %s", e)
