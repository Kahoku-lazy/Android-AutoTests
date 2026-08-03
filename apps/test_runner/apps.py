import logging

from django.apps import AppConfig

_log = logging.getLogger("test_runner.startup")


class TestRunnerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.test_runner"
    verbose_name = "执行引擎"

    def ready(self):
        """On startup: recover queued tasks + mark orphan tasks and stale runs.

        只在 ASGI 服务进程（Daphne）执行。管理命令（shell/migrate/test）和
        AgentScope 进程绝不能触发恢复——否则会把 Daphne 进程里正在执行的任务
        误判为孤儿、中断并释放其设备。
        """
        import os
        import sys

        argv = " ".join(sys.argv)
        is_asgi_server = (
            os.environ.get("DJANGO_ASGI_SERVER") == "1" or "daphne" in argv or "runserver" in argv
        )
        if not is_asgi_server:
            return

        try:
            from .models import TaskCard
            from .recovery_helpers import queue_payload_from_taskcard
            from .runner import _device_busy, is_device_busy
            from .state_machine import recover_orphans, repair_queued_terminal_drift
            from .views import _device_queue, _enqueue, _schedule_next_queued

            # 1. Clear in-memory device busy — fresh start, no devices are running
            _device_busy.clear()

            # 2. Atomic orphan recovery: TaskCard(running)→interrupted
            #    + TestRunRecord(RUNNING)→FAILED in one function
            recovered = recover_orphans()
            repaired = repair_queued_terminal_drift()
            if recovered["tasks"] or recovered["runs"] or repaired:
                _log.info(
                    "Startup recovery: %d task(s) interrupted, %d stale run(s) → FAILED",
                    recovered["tasks"],
                    recovered["runs"],
                )

            # 3. Recover queued tasks into memory queues
            queued = TaskCard.objects.filter(status="queued").order_by("created_at")
            for tc in queued:
                serial = tc.device_serial
                if serial:
                    existing = _device_queue.get(serial, [])
                    already_enqueued = any(
                        item.get("client_task_id") == tc.task_id for item in existing
                    )
                    if not already_enqueued:
                        _enqueue(serial, queue_payload_from_taskcard(tc))
            if queued:
                _log.info("Recovered %d queued task(s) from DB", queued.count())

            # 4. Kick off queued tasks for idle devices
            import asyncio

            for serial in {tc.device_serial for tc in queued if tc.device_serial}:
                if _device_queue.get(serial) and not is_device_busy(serial):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            _schedule_next_queued(serial)
                    except RuntimeError:
                        pass
        except Exception as e:
            _log.exception("Startup recovery failed: %s", e)
