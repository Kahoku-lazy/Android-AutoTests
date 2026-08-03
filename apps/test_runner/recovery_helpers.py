"""任务卡片孤儿检测 — 避免将「已分配 run_id 但未入 _active_runs」的任务误判为中断。"""

import threading

_recovery_lock = threading.Lock()


def get_protected_running_task_ids() -> set[str]:
    """返回不应被标为 interrupted 的 client_task_id 集合。

    保护两类任务：
    1. 已分配 run_id、等待 delayed_execute / u2 连接（在 _run_client_task 中）
    2. 已在 _active_runs 中实际执行
    """
    from .runner import _active_runs
    from .views import _run_client_task

    protected: set[str] = set(_run_client_task.values())

    for run_id in _active_runs:
        tid = _run_client_task.get(run_id, "")
        if tid:
            protected.add(tid)

    return {tid for tid in protected if tid}


def recover_stale_running_taskcards() -> int:
    """仅将真正孤儿的 running TaskCard 标为 interrupted。返回修复数量。

    保护逻辑（两层）：
    1. 进程内存保护列表（_run_client_task + _active_runs）
    2. 活跃时间窗口：如果关联的 TestRunRecord 在 2 分钟内创建，说明有其他进程
       （如 CLI）正在执行，不应标记为孤儿。
    """
    from datetime import timedelta

    from django.utils.timezone import now as tz_now

    from .models import TaskCard

    with _recovery_lock:
        protected = get_protected_running_task_ids()
        stale = TaskCard.objects.filter(status="running").exclude(task_id__in=protected)

        # 排除最近 2 分钟内有活跃 TestRunRecord 的卡片（跨进程保护）
        recent_cutoff = (tz_now() - timedelta(minutes=2)).isoformat()
        stale = stale.exclude(
            run__isnull=False,
            run__started_at__gt=recent_cutoff,
        )

        count = stale.count()
        if count:
            stale.update(status="done", running=False, outcome="interrupted")
        return count


def queue_payload_from_taskcard(tc, package_name: str = "") -> dict:
    """从 TaskCard 构建内存队列 payload（含定时参数）。"""
    return {
        "case_ids": tc.case_ids,
        "loop_count": tc.loop_count,
        "interval_seconds": tc.interval_seconds,
        "package_name": package_name,
        "start_at": tc.start_at or None,
        "end_at": tc.end_at or None,
        "client_task_id": tc.task_id,
    }
