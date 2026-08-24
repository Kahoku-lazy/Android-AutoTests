"""test-runner HTTP routes — 10 endpoints under /api/runner/*."""

import asyncio
import functools
import logging

from asgiref.sync import sync_to_async as _original_sta
from django.http import JsonResponse


# All sync_to_async in this file use thread_sensitive=False to avoid capturing
# the request-scoped CurrentThreadExecutor which dies after the HTTP response,
# breaking all background tasks (delayed_execute / _execute_tests / etc).
# None of our code relies on thread-sensitive DB state.
# v2: added close_old_connections() before each call + retry on DB errors to
# prevent background task hangs caused by stale/broken MySQL connections in the
# thread pool.
def _sta(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        import logging
        import time

        from django.db import OperationalError, ProgrammingError, close_old_connections

        _bg_log = logging.getLogger("test_runner.bg")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                close_old_connections()
                return fn(*args, **kwargs)
            except (OperationalError, ProgrammingError) as e:
                if attempt < max_retries - 1:
                    wait = 1 * (attempt + 1)
                    _bg_log.warning(
                        f"_sta retry {attempt + 1}/{max_retries} after {e.__class__.__name__}: {e}"
                    )
                    time.sleep(wait)
                else:
                    raise

    return _original_sta(wrapper, thread_sensitive=False)


# Drop-in replacements for @sync_to_async decorator and sync_to_async(func)() calls
_bg_sync = _sta  # decorator: @_bg_sync
sync_to_async = _sta  # inline:   sync_to_async(func)(args)

from apps.device_pool.api import release_device as dp_release_device
from models.test_models import TaskOutcome, TestRunStatus

from .. import state_machine as sm
from ..callbacks import test_callbacks
from ..models import TaskCard
from ..runner import (
    mark_device_idle,
)


def require_auth(view_func):
    """Decorator: enforce JWT authentication. Returns 401 if no valid token.
    Supports both sync and async view functions."""
    import inspect

    from functools import wraps

    if inspect.iscoroutinefunction(view_func):

        @wraps(view_func)
        async def async_wrapper(request, *args, **kwargs):
            user_id = getattr(request, "user_id", None)
            if not user_id:
                return JsonResponse(
                    {"status": False, "message": "未登录或 token 已过期"}, status=401
                )
            return await view_func(request, *args, **kwargs)

        return async_wrapper
    else:

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id = getattr(request, "user_id", None)
            if not user_id:
                return JsonResponse(
                    {"status": False, "message": "未登录或 token 已过期"}, status=401
                )
            return view_func(request, *args, **kwargs)

        return wrapper


# Per-device task queue: serial → [request_payload]
_device_queue: dict[str, list] = {}
# Per-device asyncio lock — atomic check→dequeue→mark_busy
_device_locks: dict[str, asyncio.Lock] = {}

# Maps run_id → client_task_id so the frontend can discover queued-task execution
_run_client_task: dict[str, str] = {}

_bg_log = logging.getLogger("test_runner.bg")

# 后台任务引用保存 —— 防止 asyncio.create_task 的 Task 被 GC 回收、异常被静默吞掉
_bg_tasks: set = set()
# run_id → 预检阶段登记(锁了手机但还没真正执行)。供 stop 打"停止标记";
# delayed_execute 据此在释放设备+标记停止后退出,避免设备锁泄漏。
# 结构: {run_id: {"stopped": bool, "serial": str, "client_task_id": str}}
_preflight_runs: dict = {}


def _spawn_bg(coro, label: str = "bg"):
    """创建后台任务并保存引用,完成时记录异常(替代 fire-and-forget 吞错)。"""
    import logging
    import traceback

    _bg_log = logging.getLogger("test_runner.bg")
    t = asyncio.create_task(coro)
    _bg_tasks.add(t)
    _bg_log.info(f"后台任务已创建: {label} (active={len(_bg_tasks)})")

    def _done(task):
        _bg_tasks.discard(task)
        if not task.cancelled():
            exc = task.exception()
            if exc is not None:
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                _bg_log.error("后台任务 %s 异常: %r\n%s", label, exc, tb)
            else:
                _bg_log.info(f"后台任务 {label} 正常完成 (remaining={len(_bg_tasks)})")
        else:
            _bg_log.info(f"后台任务 {label} 被取消 (remaining={len(_bg_tasks)})")

    t.add_done_callback(_done)
    return t


# u2.connect() 超时上限（秒）—— USB 松动 / ATX agent 卡死时快速失败，
# 避免阻塞占用 _device_executor 线程 / Daphne 事件循环。
U2_CONNECT_TIMEOUT = 15


def _enqueue(serial: str, payload: dict):
    """Add a test request to the device's queue."""
    _device_queue.setdefault(serial, []).append(payload)


def _enqueue_front(serial: str, payload: dict):
    """Re-insert a dequeued task at the front (e.g. after acquire failure)."""
    _device_queue.setdefault(serial, []).insert(0, payload)


def _device_lock(serial: str) -> asyncio.Lock:
    if serial not in _device_locks:
        _device_locks[serial] = asyncio.Lock()
    return _device_locks[serial]


def _dequeue(serial: str) -> dict | None:
    """Pop the next queued request for a device."""
    q = _device_queue.get(serial)
    if q:
        return q.pop(0)
    return None


def _queue_size(serial: str) -> int:
    """Number of tasks waiting for a device."""
    return len(_device_queue.get(serial, []))


def _schedule_next_queued(serial: str):
    """Fire-and-forget: start the next queued task for a device."""
    if serial:
        from .execution import _start_next_queued  # lazy to avoid circular import

        _spawn_bg(_start_next_queued(serial), f"next_queued:{serial}")


async def _enqueue_taskcard(client_task_id: str, serial: str):
    """Route a TaskCard IDLE → QUEUED through the state machine.

    Used when a device is busy and the task is parked in the in-memory queue.
    Idempotent + fault-tolerant: never raises to the caller.
    """
    if not client_task_id:
        return

    @_bg_sync
    def _do():
        try:
            tc = TaskCard.objects.get(task_id=client_task_id)
        except TaskCard.DoesNotExist:
            return
        try:
            sm.enqueue(tc, serial)
        except sm.InvalidTransition as e:
            _bg_log.warning("enqueue transition %s: %s", client_task_id, e)
        except Exception:
            _bg_log.exception("enqueue %s failed", client_task_id)

    await _do()


async def _abort_run_before_execute(
    run_id: str,
    serial: str,
    client_task_id: str,
    error: str,
    outcome: str = TaskOutcome.ERROR.value,
):
    """执行前退出(设备检查失败 / 执行前异常 / 用户中途停止):
    释放设备、把 TaskCard 推到 done 终态、通知前端。outcome='error' 或 'stopped'。
    """
    import logging

    _log = logging.getLogger("test_runner.bg")
    _log.info(f"_abort_run_before_execute: {run_id} error={error} outcome={outcome}")
    icon = "⏹" if outcome == TaskOutcome.STOPPED.value else "❌"
    await test_callbacks.on_log(run_id, f"{icon} {error}")
    # 停止是用户主动行为,不当作"设备错误"上报(避免前端标红为 error)
    if outcome != TaskOutcome.STOPPED.value:
        await test_callbacks.on_device_error(run_id, error)
    # AI 路径（无 TaskCard）：把 start_run 预建的记录置为终态，
    # 让 get_run_status 可见失败原因（WS 事件在 AI 对话场景无订阅者）
    if not client_task_id:
        from ..api import mark_run_failed

        mark_run_failed(
            run_id,
            error,
            status=(
                TestRunStatus.STOPPED.value
                if outcome == TaskOutcome.STOPPED.value
                else TestRunStatus.FAILED.value
            ),
        )
    mark_device_idle(serial)
    try:
        await sync_to_async(dp_release_device)(serial, reason="manual")
    except Exception:
        _bg_log.exception("release after pre-run abort (%s)", serial)
    if client_task_id:

        @_bg_sync
        def mark_terminal():
            try:
                tc = TaskCard.objects.get(task_id=client_task_id)
            except TaskCard.DoesNotExist:
                return
            # 走完整合法路径 idle→queued→running→done,dequeue 建一条审计 TestRunRecord
            try:
                sm.enqueue(tc, serial)
                rec = sm.dequeue(tc, run_id, serial, [], tc.loop_count or 1)
                sm.fail(tc, rec, outcome=outcome)
            except sm.InvalidTransition as e:
                _bg_log.warning("pre-run mark %s: %s", client_task_id, e)
            except Exception:
                _bg_log.exception("pre-run mark task %s failed", client_task_id)

        try:
            await mark_terminal()
        except Exception:
            _bg_log.exception("pre-run mark task %s failed", client_task_id)
    _run_client_task.pop(run_id, None)
    _preflight_runs.pop(run_id, None)
    _schedule_next_queued(serial)
