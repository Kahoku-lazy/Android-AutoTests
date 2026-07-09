from django.apps import AppConfig


class TestRunnerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.test_runner'
    verbose_name = '执行引擎'

    def ready(self):
        """On startup: recover queued tasks + mark orphan tasks and stale runs."""
        try:
            from .state_machine import recover_orphans
            from .models import TaskCard
            from .views import _enqueue, _device_queue, _schedule_next_queued
            from .runner import is_device_busy, _device_busy

            # 1. Clear in-memory device busy — fresh start, no devices are running
            _device_busy.clear()

            # 2. Atomic orphan recovery: TaskCard(running)→interrupted
            #    + TestRunRecord(RUNNING)→FAILED in one function
            recovered = recover_orphans()
            if recovered['tasks'] or recovered['runs']:
                print(f"[test_runner] Startup recovery: "
                      f"{recovered['tasks']} task(s) interrupted, "
                      f"{recovered['runs']} stale run(s) → FAILED")

            # 3. Recover queued tasks into memory queues
            queued = TaskCard.objects.filter(status='queued').order_by('created_at')
            for tc in queued:
                serial = tc.device_serial
                if serial:
                    _enqueue(serial, {
                        "case_ids": tc.case_ids,
                        "loop_count": tc.loop_count,
                        "interval_seconds": tc.interval_seconds,
                        "package_name": "",
                        "start_at": None,
                        "end_at": None,
                        "client_task_id": tc.task_id,
                    })
            if queued:
                print(f"[test_runner] Recovered {queued.count()} queued task(s) from DB")

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
            import traceback
            print(f"[test_runner] Startup recovery failed: {e}")
            traceback.print_exc()
