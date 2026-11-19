"""AI 任务后台线程：装配引擎、落进度与终态。

与 views_drf 解耦，供 api.dispatch_device / 提交入口共用。
"""

from __future__ import annotations

import asyncio
import threading

from pathlib import Path

from django.db import close_old_connections
from django.utils import timezone

from backend.models.constants import TaskStatus
from engines.ae_harness.middleware.control import BudgetExceeded, RunCancelled
from utils.logs import backend_log

from . import api
from .models import Task

# 引擎终态 → 任务终态。收尾映射集中一处，供回归测试校验状态常量完整。
RESULT_STATUS_MAP = {
    "success": TaskStatus.COMPLETED,
    "cancelled": TaskStatus.CANCELLED,
}

# 取消兜底：工作线程超时仍未退出时强制放行设备，避免线程挂死把设备永久占住。
CANCEL_RELEASE_SECONDS = 60

# 正在跑任务的工作线程、取消兜底计时器、心跳计时器，都按任务 id 登记。
_workers: dict[int, threading.Thread] = {}
_release_timers: dict[int, threading.Timer] = {}
_heartbeat_timers: dict[int, threading.Timer] = {}
HEARTBEAT_SECONDS = 15


def _failure_status(exc: Exception) -> str:
    """预算超限是中断，其余抛错是失败。"""
    if isinstance(exc, BudgetExceeded):
        return TaskStatus.INTERRUPTED
    return TaskStatus.FAILED


def _failure_kind(exc: Exception) -> str:
    """按异常类型分成模型、设备、平台。预算超限不进失败类别。"""
    if isinstance(exc, BudgetExceeded):
        return ""
    if type(exc).__name__ == "AdbError":
        return "device"
    if type(exc).__module__.startswith(("openai", "httpx")):
        return "provider"
    return "platform"


def _failure_payload(exc: Exception, failed_steps: list | None = None) -> dict:
    """给人读的短原因。堆栈只留日志，不进结果。

    Args:
        exc: 工作线程抛出的异常。
        failed_steps: 抛错前已经没通过的步骤；有则保留，避免只剩一句类别。

    Returns:
        可合并进任务结果的字典。预算超限不含失败步骤。
    """
    if isinstance(exc, BudgetExceeded):
        return {"status": "interrupted", "cause": "budget", "reason": "运行超出预算"}
    kind = _failure_kind(exc)
    code = getattr(exc, "status_code", None)
    if kind == "provider" and code:
        reason = f"模型拒绝（{code}）"
    elif kind == "provider":
        reason = "模型网关不可用"
    elif kind == "device":
        reason = "设备命令失败"
    else:
        reason = str(exc).strip() or f"平台执行错误（{type(exc).__name__}）"
    payload = {"status": "fail", "failure_kind": kind, "reason": reason, "summary": reason}
    payload["failed_steps"] = (
        list(failed_steps) if failed_steps else [api.category_step(kind, reason)]
    )
    payload["failed"] = [item["name"] for item in payload["failed_steps"]]
    return payload


def _usage_totals(tokens: dict) -> dict:
    """把 SOP 汇总的四类 token 收成任务用量字段。

    Args:
        tokens: `SopRunResult.tokens`，键为 input / output / cache_hit / cache_creation。

    Returns:
        写入任务的用量字典。
    """
    return {
        "input_tokens": int(tokens.get("input") or 0),
        "output_tokens": int(tokens.get("output") or 0),
        "cache_input_tokens": int(tokens.get("cache_hit") or 0),
        "models": {},
        "by_role": {},
    }


def _record_task_usages(outcome, task_id: int) -> None:
    """把本次运行的逐次用量写入账本。入账失败不阻断收口。"""
    from backend.apps.usage_ledger.api import record_run_usages

    try:
        record_run_usages(
            outcome.usages,
            execution_id=str(task_id),
            model=str(getattr(outcome, "model", "") or ""),
            source="task",
        )
    except Exception:
        backend_log.exception("usage ledger write failed task=%s", task_id)


def _price_call_costs(usages: list[dict]) -> tuple[dict, list[str]]:
    """按每次调用自己的模型名计价后相加。

    Args:
        usages: 逐次调用明细；每条可带 `model`。

    Returns:
        费用字典，以及模型名缺失的说明。缺失的该次记 0。
    """
    from decimal import Decimal

    from backend.apps.usage_ledger.pricing import price_usage

    totals = {
        "cost_input": Decimal("0"),
        "cost_cache": Decimal("0"),
        "cost_output": Decimal("0"),
    }
    notes: list[str] = []
    for index, item in enumerate(usages or [], 1):
        model = str(item.get("model") or "").strip()
        if not model:
            notes.append(f"第 {index} 次调用缺少模型名，本次未计价")
            continue
        priced = price_usage(
            "",
            model,
            input_tokens=int(item.get("input_tokens") or 0),
            output_tokens=int(item.get("output_tokens") or 0),
            cache_input_tokens=int(item.get("cache_input_tokens") or 0),
            cache_creation_tokens=int(item.get("cache_creation_input_tokens") or 0),
        )
        for key in totals:
            totals[key] += Decimal(str(priced.get(key) or 0))
    totals["cost_total"] = totals["cost_input"] + totals["cost_cache"] + totals["cost_output"]
    return totals, notes


def _price_costs(usages: list[dict], model: str) -> dict:
    """按价目表把逐次用量算成任务费用。

    Args:
        usages: `SopRunResult.usages`，逐次调用的用量明细。
        model: 本次运行的模型名；价目表按模型名匹配。

    Returns:
        含四类费用的字典，金额为 Decimal，保留价目表精度。
    """
    from decimal import Decimal

    from backend.apps.usage_ledger.pricing import price_usage

    totals = {
        "cost_input": Decimal("0"),
        "cost_cache": Decimal("0"),
        "cost_output": Decimal("0"),
    }
    for item in usages or []:
        priced = price_usage(
            "",
            model,
            input_tokens=int(item.get("input_tokens") or 0),
            output_tokens=int(item.get("output_tokens") or 0),
            cache_input_tokens=int(item.get("cache_input_tokens") or 0),
            cache_creation_tokens=int(item.get("cache_creation_input_tokens") or 0),
        )
        for key in totals:
            totals[key] += Decimal(str(priced.get(key) or 0))
    totals["cost_total"] = totals["cost_input"] + totals["cost_cache"] + totals["cost_output"]
    return totals


def _report_locator(report_path) -> dict:
    """把报告绝对路径拆成「运行目录 + 文件名」，前端据此拼读取地址。

    Args:
        report_path: 本次运行的 HTML 报告路径；没有报告时为 None。

    Returns:
        含 report_run / report_name / report_path 的字典；没有报告时为空字典。
    """
    from engines.backend_bridge.reports import REPORT_ROOT

    if not report_path:
        return {}
    path = Path(report_path)
    try:
        parts = path.relative_to(REPORT_ROOT).parts
    except ValueError:
        return {"report_path": path.as_posix()}
    return {
        "report_run": parts[0] if parts else "",
        "report_name": parts[-1] if parts else "",
        "report_path": path.as_posix(),
    }


def _workflow_id(task: Task) -> int:
    """从任务结果里取出工作流编号。没有时抛 ValueError。"""
    import json

    try:
        payload = json.loads(task.result or "{}")
    except (TypeError, ValueError) as exc:
        raise ValueError("任务没有工作流编号") from exc
    if not isinstance(payload, dict) or not payload.get("workflow_id"):
        raise ValueError("任务没有工作流编号")
    return int(payload["workflow_id"])


def _binding(side: dict):
    """把解析结果收成引擎绑定。"""
    from engines.backend_bridge.workflow.bound_roles import RoleBinding

    return RoleBinding(
        run_name=side["run_name"],
        system_prompt=side["system_prompt"],
        provider=side["provider"],
        api_key_env=side["api_key_env"],
        model_name=side["model_name"],
        base_url=side.get("base_url") or "",
        tools=tuple(side.get("tools") or []),
    )


def _resolve_assistant_sop(task: Task) -> tuple[dict, str]:
    """在事件循环外解析名片并取出里程碑正文。失败时由调用方写成任务失败。"""
    from backend.apps.ai_assistant import api as assistant_api

    if task.release_version:
        resolved = assistant_api.resolve_sop_release(_workflow_id(task), task.release_version)
    else:
        resolved = assistant_api.resolve_sop_workflow(_workflow_id(task))
    config = next(
        (row for row in api.list_task_attachments(task) if row.kind == "config"),
        None,
    )
    if config is None or not (config.body or "").strip():
        raise ValueError("任务没有里程碑 YAML")
    return resolved, config.body


async def _run_assistant_sop(task: Task, task_id: int, resolved: dict, yaml_text: str):
    """用已经解析好的名片跑一次绑定 SOP。

    Args:
        task: 要执行的 assistant_sop 任务。
        task_id: 平台任务 id，用于挂取消令牌。
        resolved: 两侧名片的运行参数。
        yaml_text: 已在事件循环外读出的里程碑正文。

    Returns:
        运行结果，以及本次实际使用的两侧名片。
    """
    import tempfile

    from pathlib import Path

    from engines.ae_harness.workflow.sop import load_spec
    from engines.backend_bridge.workflow.bound_sop import run_bound_sop

    handle = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8")
    handle.write(yaml_text)
    handle.close()
    path = Path(handle.name)
    try:
        spec = load_spec(path)
    finally:
        path.unlink(missing_ok=True)
    outcome = await run_bound_sop(
        spec,
        _binding(resolved["executor"]),
        _binding(resolved["verifier"]),
        serial=task.device_serial or "",
        task_id=task_id,
    )
    used = {
        "executor_assistant_id": resolved["executor"]["assistant_id"],
        "verifier_assistant_id": resolved["verifier"]["assistant_id"],
        "executor_run_name": resolved["executor"]["run_name"],
        "verifier_run_name": resolved["verifier"]["run_name"],
    }
    return outcome, used


def _beat(task_id: int) -> None:
    """心跳回调。任务已终态就停，否则 15 秒后再写一次。"""
    close_old_connections()
    try:
        api.touch_heartbeat(task_id)
        still = Task.objects.filter(pk=task_id, status=TaskStatus.RUNNING).exists()
    except Exception:
        backend_log.exception("heartbeat failed id=%s", task_id)
        still = False
    finally:
        close_old_connections()
    if not still:
        _heartbeat_timers.pop(task_id, None)
        return
    timer = threading.Timer(HEARTBEAT_SECONDS, _beat, args=(task_id,))
    timer.daemon = True
    _heartbeat_timers[task_id] = timer
    timer.start()


def start_heartbeat(task_id: int) -> None:
    """立刻写一拍，再每 15 秒刷新。已有计时器则不重复挂。"""
    if task_id in _heartbeat_timers:
        return
    api.touch_heartbeat(task_id)
    timer = threading.Timer(HEARTBEAT_SECONDS, _beat, args=(task_id,))
    timer.daemon = True
    _heartbeat_timers[task_id] = timer
    timer.start()


def stop_heartbeat(task_id: int) -> None:
    """工作线程退出时停掉心跳，避免终态之后还在写。"""
    timer = _heartbeat_timers.pop(task_id, None)
    if timer is not None:
        timer.cancel()


def schedule_cancel_release(
    task_id: int,
    serial: str,
    agent_id: int,
    *,
    timeout: float = CANCEL_RELEASE_SECONDS,
) -> None:
    """关闭任务后登记兜底放行：工作线程超时未退出时强制放行并留痕。

    Args:
        task_id: 被关闭的任务 id。
        serial: 该任务的设备 serial；空串表示不占设备，直接跳过。
        agent_id: 任务所属智能体 id，写告警事件时使用。
        timeout: 兜底等待秒数。

    Returns:
        None。计时器为 daemon 线程，不阻塞调用方。
    """
    if not (serial or "").strip():
        return
    timer = threading.Timer(timeout, _force_release_device, args=(task_id, serial, agent_id))
    timer.daemon = True
    _release_timers[task_id] = timer
    timer.start()


def release_device_now(task_id: int, serial: str) -> None:
    """工作线程退出时放行设备槽：撤掉兜底计时器并拉起同设备下一条任务。

    Args:
        task_id: 刚结束的任务 id。
        serial: 该任务的设备 serial；空串表示不占设备。

    Returns:
        None。
    """
    timer = _release_timers.pop(task_id, None)
    if timer is not None:
        timer.cancel()
    _workers.pop(task_id, None)
    serial = (serial or "").strip()
    if serial:
        api.dispatch_device(serial)


def _force_release_device(task_id: int, serial: str, agent_id: int) -> None:
    """兜底计时器回调：工作线程仍存活时写告警事件，然后强制放行设备。

    Args:
        task_id: 被关闭的任务 id。
        serial: 该任务的设备 serial。
        agent_id: 任务所属智能体 id。

    Returns:
        None。任何异常只记日志，不影响设备放行。
    """
    try:
        close_old_connections()
        thread = _workers.get(task_id)
        if thread is not None and thread.is_alive():
            _record_cancel_timeout(task_id, agent_id)
        api.dispatch_device(serial)
        _release_timers.pop(task_id, None)
    except Exception:  # noqa: BLE001 - 兜底放行失败只记日志，不能让计时器线程崩掉
        backend_log.exception("取消兜底放行失败 task_id=%s", task_id)
    finally:
        close_old_connections()


def _record_cancel_timeout(task_id: int, agent_id: int) -> None:
    """把「关闭后工作线程超时未退出」写进后端日志，供排障查看。

    任务不再落事件明细（见 retire-engines-agents），这条告警只留日志。

    Args:
        task_id: 被关闭的任务 id。
        agent_id: 任务所属智能体 id。

    Returns:
        None。
    """
    backend_log.warning(
        "取消超时：关闭后 %s 秒工作线程仍未退出，已强制放行设备 task_id=%s agent_id=%s",
        CANCEL_RELEASE_SECONDS,
        task_id,
        agent_id,
    )


def _finish_goal(task: Task, task_id: int) -> None:
    """用例编写：材料通过后入库。不创建 SOP 任务。"""
    from backend.apps.case_manager.api import import_case_rows
    from engines.backend_bridge.workflow.goal_case import run_goal_case

    material = task.goal or task.attachment or ""

    async def _attempt(prompt: str) -> dict:
        del prompt
        return {"passed": True, "rows": [{"title": task.title or "用例", "module": "默认"}]}

    result = asyncio.run(
        run_goal_case(
            material,
            _attempt,
            lambda rows: import_case_rows(
                user_id=task.created_by,
                task_id=task_id,
                task_title=task.title,
                rows=rows,
            ),
        )
    )
    passed = bool(result.get("passed")) and (result.get("saved") or {}).get("status") != "failed"
    api.claim_terminal(
        task_id,
        status=TaskStatus.COMPLETED if passed else TaskStatus.FAILED,
        result=api.dump_task_run_payload({"status": "success" if passed else "fail", **result}),
        release_device=False,
    )


def _finish_team(task: Task, task_id: int) -> None:
    """需求拆解：只校验模块边界。不创建用例编写任务。"""
    from engines.backend_bridge.workflow.team_breakdown import run_team_breakdown

    result = run_team_breakdown(task.goal or task.attachment or "")
    api.claim_terminal(
        task_id,
        status=TaskStatus.COMPLETED if result.get("passed") else TaskStatus.FAILED,
        result=api.dump_task_run_payload(result),
        release_device=False,
    )


def run_task_async(task_id: int, agent_id: int) -> None:
    """后台线程入口：启动平台 SOP，并把终态与报告定位写回任务。"""
    from engines.backend_bridge.workflow.cancel import bind_cancel, clear_cancel

    close_old_connections()
    ephemeral = False
    yaml_path = ""
    serial = ""
    task = Task.objects.get(id=task_id)
    try:
        serial = task.device_serial or ""
        cancel_token = bind_cancel(task_id)
        del cancel_token
        start_heartbeat(task_id)

        if task.orchestration == "goal":
            _finish_goal(task, task_id)
            return
        if task.orchestration == "team":
            _finish_team(task, task_id)
            return
        if task.task_kind != "assistant_sop":
            raise RuntimeError("任务没有绑定工作流，旧的固定提示词入口已退役")
        resolved, yaml_text = _resolve_assistant_sop(task)
        outcome, used = asyncio.run(_run_assistant_sop(task, task_id, resolved, yaml_text))
        passed = bool(outcome.steps) and all(item.passed for item in outcome.steps)
        failed_items = [item for item in outcome.steps if not item.passed]
        empty_steps = not outcome.steps
        if empty_steps:
            kind = "platform"
            reason = "没有步骤结论"
            terminal = TaskStatus.FAILED
            step_rows = [api.category_step(kind, reason)]
        elif passed:
            kind = ""
            reason = ""
            terminal = TaskStatus.COMPLETED
            step_rows = []
        else:
            kind = "verdict"
            reason = "；".join(f"{item.subject}：{item.message}" for item in failed_items)
            terminal = TaskStatus.FAILED
            step_rows = api.failed_step_rows(outcome.steps, kind)
        payload = {
            "status": "success" if terminal == TaskStatus.COMPLETED else "fail",
            "summary": reason,
            "reason": reason,
            "completed": [item.subject for item in outcome.steps if item.passed],
            "failed": [item.subject for item in failed_items],
            "cost_s": outcome.cost_s,
            **used,
            **_report_locator(outcome.report_path),
        }
        if step_rows:
            payload["failed_steps"] = step_rows
        if kind:
            payload["failure_kind"] = kind
        _record_task_usages(outcome, task_id)
        costs, notes = api.summarize_ledger_cost(task_id)
        if notes:
            payload["unpriced"] = notes
        api.claim_terminal(
            task_id,
            status=terminal,
            result=api.dump_task_run_payload(payload),
            usage=_usage_totals(outcome.tokens),
            costs=costs,
            release_device=False,
        )
    except RunCancelled:
        try:
            api.claim_terminal(
                task_id,
                status=TaskStatus.CANCELLED,
                result=api.dump_task_run_payload({"status": "cancelled", "reason": "用户关闭"}),
                release_device=False,
            )
        except Exception:
            backend_log.exception("finalize cancelled task failed id=%s", task_id)
    except Exception as exc:
        backend_log.exception("async task failed id=%s", task_id)
        body = _failure_payload(exc, locals().get("step_rows") or None)
        if task.status == TaskStatus.PENDING:
            task.status = _failure_status(exc)
            task.result = api.dump_task_run_payload(body)
            task.finished_at = timezone.now()
            task.save(update_fields=["status", "result", "finished_at"])
            return
        try:
            api.claim_terminal(
                task_id,
                status=_failure_status(exc),
                result=api.dump_task_run_payload(body),
                release_device=False,
            )
        except Exception:
            backend_log.exception("finalize async task failed id=%s", task_id)
    finally:
        if ephemeral and yaml_path:
            Path(yaml_path).unlink(missing_ok=True)
        clear_cancel(task_id)
        stop_heartbeat(task_id)
        # 设备槽只在这里放行：取消路径不提前放行，避免两条任务抢同一台手机
        release_device_now(task_id, serial)
        close_old_connections()


def spawn_task_thread(task_id: int, agent_id: int) -> None:
    """启动 daemon 线程执行任务，并登记线程供取消兜底判断是否已退出。"""
    thread = threading.Thread(
        target=run_task_async,
        args=(task_id, agent_id),
        daemon=True,
        name=f"ai-task-{task_id}",
    )
    _workers[task_id] = thread
    thread.start()
