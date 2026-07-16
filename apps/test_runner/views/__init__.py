"""test-runner HTTP routes — re-exports from sub-modules.

Backward-compatible: external callers (urls.py, apps.py, recovery_helpers.py)
continue to import from apps.test_runner.views as before.
"""
from .helpers import (
    # Shared state
    _device_queue,
    _run_client_task,
    # Utility functions
    _sta,
    sync_to_async,
    _bg_sync,
    require_auth,
    _spawn_bg,
    _enqueue,
    _enqueue_front,
    _device_lock,
    _dequeue,
    _queue_size,
    _schedule_next_queued,
    _enqueue_taskcard,
    _abort_run_before_execute,
    _bg_tasks,
    _preflight_runs,
)

from .execution import (
    start_test_run,
    _start_next_queued,
)

from .executor import (
    _execute_tests,
)

from .run_views import (
    stop_test_run,
    cancel_queued_task,
    list_active,
    test_run_status,
    list_test_runs,
)

from .task_views import (
    run_single_step,
    task_card_list,
    task_card_save,
    task_card_delete,
    run_monitor,
    run_snapshot,
)

__all__ = [
    # Helpers
    '_device_queue', '_run_client_task',
    '_sta', 'sync_to_async', '_bg_sync', 'require_auth',
    '_spawn_bg', '_enqueue', '_enqueue_front', '_device_lock',
    '_dequeue', '_queue_size', '_schedule_next_queued',
    '_enqueue_taskcard', '_abort_run_before_execute',
    '_bg_tasks', '_preflight_runs',
    # Execution
    'start_test_run', '_start_next_queued',
    # Executor
    '_execute_tests',
    # Run views
    'stop_test_run', 'cancel_queued_task', 'list_active',
    'test_run_status', 'list_test_runs',
    # Task views
    'run_single_step', 'task_card_list', 'task_card_save',
    'task_card_delete', 'run_monitor', 'run_snapshot',
]
