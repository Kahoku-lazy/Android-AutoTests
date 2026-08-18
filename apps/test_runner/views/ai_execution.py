"""AI 工具触发的单设备 UI 执行编排（运行于 Daphne 主循环）。

由 `api.start_run` 通过 `run_coroutine_threadsafe` 投递到主循环执行。
复用 test_runner 的「预检连接 → _execute_tests」生命周期，不含调度/队列/TaskCard。
"""

from apps.device_pool.api import acquire_device as dp_acquire_device
from apps.device_pool.api import release_device as dp_release_device

from ..callbacks import test_callbacks
from ..executors.ui.connect import DeviceCheckError, check_and_connect_async
from ..runner import TestRunner, mark_device_busy, mark_device_idle
from ..runner import _device_executor as _u2_executor
from .executor import _execute_tests
from .helpers import (
    _abort_run_before_execute,
    _bg_log,
    _preflight_runs,
    _schedule_next_queued,
    sync_to_async,
)


def _device_user_id(user_id: str):
    """与 ai_assistant 的 acquire_device 工具保持一致的身份（int(user_id)）。"""
    try:
        return int(user_id)
    except (ValueError, TypeError):
        return user_id or "ai-anonymous"


async def _run_ui_for_ai(
    run_id: str,
    test_cases: list,
    loop_count: int,
    interval_seconds: int,
    package_name: str,
    serial: str,
    user_id: str = "",
) -> None:
    """在指定设备上执行 UI 测试（AI run_test 工具的真实执行体）。

    生命周期：权威锁设备 → 预检连接 → _execute_tests → finally 释放兜底。
    结果经 WebSocket 推送 + DB 持久化，本函数不返回值。
    """
    # ── 1. 权威设备锁（幂等：AI 可能已 acquire；被他人占用则放弃，绝不释放他人设备）──
    try:
        await sync_to_async(dp_acquire_device)(
            serial, user_id=_device_user_id(user_id), timeout=3600
        )
    except ValueError as e:
        await test_callbacks.on_log(run_id, f"❌ {e}")
        await test_callbacks.on_device_error(run_id, str(e))
        return

    mark_device_busy(serial)
    pending_release = True

    try:
        _preflight_runs[run_id] = {"stopped": False, "serial": serial, "client_task_id": ""}

        # ── 2. 预检连接 ──
        try:
            d = await check_and_connect_async(serial, run_id, test_callbacks, _u2_executor)
        except DeviceCheckError as e:
            await _abort_run_before_execute(run_id, serial, "", f"手机连接不上: {e}")
            pending_release = False
            return
        except Exception as e:
            await _abort_run_before_execute(run_id, serial, "", f"执行前异常: {e}")
            pending_release = False
            return

        # ── 3. 连接期间被停止 ──
        if _preflight_runs.get(run_id, {}).get("stopped"):
            await _abort_run_before_execute(run_id, serial, "", "任务已被停止", outcome="stopped")
            pending_release = False
            return

        # ── 4. 交接给执行（_execute_tests.finally 负责释放设备）──
        _preflight_runs.pop(run_id, None)
        await test_callbacks.on_run_started(run_id)
        pending_release = False
        runner = TestRunner(d, package_name, callback=test_callbacks)
        await _execute_tests(run_id, runner, test_cases, loop_count, interval_seconds, serial)
    except Exception as e:
        _bg_log.exception("ai run failed %s", run_id)
        await _abort_run_before_execute(run_id, serial, "", str(e))
    finally:
        # 兜底：拿到锁却未交接执行、也未走 abort 的异常退出，确保释放设备（幂等）
        if pending_release:
            mark_device_idle(serial)
            try:
                await sync_to_async(dp_release_device)(serial, reason="manual")
            except Exception:
                _bg_log.exception("ai release %s failed", serial)
            _preflight_runs.pop(run_id, None)
            _schedule_next_queued(serial)
