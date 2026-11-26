import os
import sys
import threading

from django.apps import AppConfig

from utils.logs import backend_log

SWEEP_INTERVAL_SECONDS = 30


class TaskListConfig(AppConfig):
    name = "backend.apps.task_list"
    label = "task_list"
    verbose_name = "任务清单"

    def ready(self):
        argv = " ".join(sys.argv)
        is_asgi_server = os.environ.get("DJANGO_ASGI_SERVER") == "1" or "daphne" in argv
        is_runserver = (
            "runserver" in argv and "makemigrations" not in argv and "migrate" not in argv
        )
        if not is_asgi_server and not is_runserver:
            return
        if (
            os.environ.get("DJANGO_AUTORELOAD_PARENT") == "1"
            and os.environ.get("RUN_MAIN") != "true"
        ):
            return

        threading.Thread(
            target=self._run_sweep_loop,
            name="task-list-sweep",
            daemon=True,
        ).start()

    def _run_sweep_loop(self) -> None:
        from django.apps import apps as django_apps

        django_apps.ready_event.wait()
        while True:
            try:
                from . import api
                from .sweep_mark import clear_stop_timeout_ids, read_stop_timeout_ids

                marked = read_stop_timeout_ids()
                recovered = api.sweep_stale_tasks(marked)
                if marked:
                    clear_stop_timeout_ids()
                if recovered:
                    backend_log.info("Sweep: %d stale running task(s) → interrupted", recovered)
            except Exception as exc:
                backend_log.exception("task sweep failed: %s", exc)
            threading.Event().wait(SWEEP_INTERVAL_SECONDS)
