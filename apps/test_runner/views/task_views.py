"""Task card + single-step + monitor endpoints."""
import json
import os
from datetime import datetime

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q

from models.step_types import TestStep

from .helpers import (
    _bg_log, _run_client_task,
    require_auth,
)

from ..runner import get_active_run
from ..models import TestResult, TestRunRecord, TaskCard
from .. import state_machine as sm


@require_auth
@csrf_exempt
def run_single_step(request):
    """POST /api/runner/run-step — Execute a single step on the current device for debugging."""
    data = json.loads(request.body) if request.body else {}
    step_type = data.get("type", "click")
    xpath = data.get("xpath", "")
    xpath2 = data.get("xpath2", "")
    timeout = data.get("timeout", 10)
    expected_text = data.get("expected_text", "")
    index = data.get("index", 0)
    direction = data.get("direction", "")
    distance = data.get("distance", 500)
    description = data.get("description", step_type)

    if step_type not in (
        "click", "long_click",
        "swipe",
        "wait", "wait_disappear", "sleep",
        "verify_text", "poll_text",
        "start_app", "kill_app",
        "perf_element_time",
        "wait_toast",
        "if_element_appear", "if_element_disappear",
        "loop_n", "loop_elements",
    ):
        return JsonResponse({"ok": False, "error": f"Unknown step type: {step_type}"})

    try:
        from ..executors.ui.adapter import DeviceAdapter
        from ..executors.ui.connect import DeviceConnection
        from ..executors.ui.executor import StepExecutor
        from apps.device_pool.api import device

        target_serial = data.get("device_serial", "").strip()
        if target_serial:
            device.switch_to(target_serial)
        elif not device.current_serial:
            return JsonResponse({"ok": False, "error": "请先在用例编辑页顶部选择调试设备"})

        step = TestStep(
            type=step_type,
            xpath=xpath,
            xpath2=xpath2,
            timeout=timeout,
            expected_text=expected_text,
            index=index,
            direction=direction,
            distance=distance,
            description=description,
        )

        logs: list[str] = []
        conn = DeviceConnection(
            serial=device.current_serial,
            airtest=device.ad,
            u2=device.u2d,
            info=device.info(),
        )
        adapter = DeviceAdapter(
            conn,
            package_name=xpath if step_type in ("start_app", "kill_app") else "",
            logger=logs.append,
        )
        executor = StepExecutor(adapter)
        result = executor.execute(step)

        if result == "pass":
            return JsonResponse(
                {
                    "ok": True,
                    "result": result,
                    "message": f"步骤「{description}」执行成功",
                    "logs": logs,
                }
            )
        return JsonResponse(
            {
                "ok": False,
                "result": result,
                "error": f"步骤「{description}」执行失败 ({result})",
                "logs": logs,
            }
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"步骤执行异常: {str(e)}"})


# ═══════════════════════════════════════════════════════
#  TaskCard CRUD — cross-device task card sync
# ═══════════════════════════════════════════════════════


def _safe_perf_stats(tc):
    """Safely extract perf stats from a TaskCard's linked run summary."""
    try:
        if tc.run_id and tc.run:
            return tc.run.summary.get("_perf") if tc.run.summary else None
    except Exception:
        pass
    return None


@require_auth
def task_card_list(request):
    """GET /api/runner/tasks — List all task cards."""
    from ..recovery_helpers import recover_stale_running_taskcards

    recover_stale_running_taskcards()
    sm.repair_queued_terminal_drift()

    qs = TaskCard.objects.all().order_by("-created_at")[:200]
    cards = []
    for tc in qs:
        cards.append(
            {
                "id": tc.task_id,
                "name": tc.name,
                "mode": tc.mode,
                "taskType": tc.task_type or "ui_automation",
                "deviceSerial": tc.device_serial,
                "caseIds": tc.case_ids,
                "loopCount": tc.loop_count,
                "intervalSeconds": tc.interval_seconds,
                # running 派生自 status，杜绝 status/running 双源不一致（僵尸"执行中"卡片）
                "running": tc.status == "running",
                "runId": tc.run.run_id if tc.run_id else "",
                "caseItems": tc.case_items,
                "stepStates": tc.step_states,
                "overallPass": tc.overall_pass,
                "overallFail": tc.overall_fail,
                "logs": tc.logs,
                "createdAt": str(tc.created_at),
                "creator": tc.creator,
                "currentCaseTitle": tc.current_case_title or "",
                "currentIteration": tc.current_iteration or 0,
                "failedSteps": tc.failed_steps,
                "status": tc.status,
                "outcome": tc.outcome,
                "round": tc.round,
                "conclusion": tc.conclusion,
                "bugTicket": tc.bug_ticket,
                "startAt": tc.start_at or "",
                "endAt": tc.end_at or "",
                "perfStats": _safe_perf_stats(tc),
                "step_details": _load_step_details(tc),
            }
        )
    return JsonResponse({"ok": True, "tasks": cards})


def _load_step_details(tc) -> list:
    """Load per-step screenshots from linked TestResult rows."""
    try:
        if not tc.run_id:
            return []
        results = TestResult.objects.filter(run_id=tc.run_id).order_by("iteration")
        all_steps = []
        for tr in results:
            details = tr.step_details or []
            for d in details:
                d.setdefault("caseId", tr.case_id)
                d.setdefault("caseTitle", _resolve_case_title(tc, tr.case_id))
                d.setdefault("_date", str(tr.created_at)[:19] if tr.created_at else "")
            all_steps.extend(details)
        return all_steps
    except Exception:
        return []


def _resolve_case_title(tc, case_id: str) -> str:
    """Try to resolve a case title from the TaskCard's case_items."""
    for ci in (tc.case_items or []):
        if str(ci.get("id", "")) == str(case_id):
            return ci.get("title", case_id)
    return case_id


@require_auth
@csrf_exempt
def task_card_save(request):
    """POST /api/runner/tasks/save — Upsert a task card."""
    data = json.loads(request.body) if request.body else {}
    task_id = data.get("id", "").strip()
    if not task_id:
        return JsonResponse({"ok": False, "error": "任务ID不能为空"}, status=400)

    defaults = {
        "name": data.get("name", ""),
        "creator": data.get("creator", ""),
        "mode": data.get("mode", "immediate"),
        "task_type": data.get("taskType", "ui_automation"),
        "device_serial": data.get("deviceSerial", ""),
        "case_ids": data.get("caseIds", []),
        "loop_count": data.get("loopCount", 1),
        "interval_seconds": data.get("intervalSeconds", 5),
        # running 不接受前端传入 —— 由后端运行时路径管理，避免与 status 漂移
        # run_id FK 由后端管理，不接受前端字符串（避免 FK 类型冲突）
        "case_items": data.get("caseItems", []),
        "step_states": data.get("stepStates", []),
        "overall_pass": data.get("overallPass", 0),
        "overall_fail": data.get("overallFail", 0),
        "logs": (data.get("logs") or [])[-200:],
        "outcome": data.get("outcome", ""),
        "round": data.get("round", 0),
        "conclusion": data.get("conclusion", ""),
        "bug_ticket": data.get("bugTicket", ""),
        "failed_steps": (data.get("failedSteps") or [])[-200:],
        "current_case_title": data.get("currentCaseTitle", ""),
        "current_iteration": int(data.get("currentIteration") or 0),
        "start_at": data.get("startAt") or "",
        "end_at": data.get("endAt") or "",
    }
    # status is backend-managed — only set on create, never overwrite from frontend
    try:
        task = TaskCard.objects.get(task_id=task_id)
        for k, v in defaults.items():
            setattr(task, k, v)
        task.save()
    except TaskCard.DoesNotExist:
        # Explicit create — every field must be set to avoid MySQL integrity errors
        task = TaskCard(
            task_id=task_id,
            name=data.get("name", ""),
            creator=data.get("creator", ""),
            mode=data.get("mode", "immediate"),
            task_type=data.get("taskType", "ui_automation"),
            device_serial=data.get("deviceSerial", ""),
            case_ids=data.get("caseIds", []),
            loop_count=data.get("loopCount", 1),
            interval_seconds=data.get("intervalSeconds", 5),
            running=False,  # 新建任务恒为未运行；执行由 POST /run 启动
            case_items=data.get("caseItems", []),
            step_states=data.get("stepStates", []),
            overall_pass=data.get("overallPass", 0),
            overall_fail=data.get("overallFail", 0),
            logs=(data.get("logs") or [])[-200:],
            outcome=data.get("outcome", ""),
            round=data.get("round", 0),
            conclusion=data.get("conclusion", ""),
            bug_ticket=data.get("bugTicket", ""),
            failed_steps=(data.get("failedSteps") or [])[-200:],
            current_case_title=data.get("currentCaseTitle", ""),
            current_iteration=int(data.get("currentIteration") or 0),
            start_at=data.get("startAt") or "",
            end_at=data.get("endAt") or "",
            status="idle",
        )
        task.save()
    return JsonResponse({"ok": True, "id": task_id})


@require_auth
@csrf_exempt
def task_card_delete(request, task_id):
    """DELETE /api/runner/tasks/{task_id} — Delete a task card."""
    try:
        TaskCard.objects.get(task_id=task_id).delete()
        return JsonResponse({"ok": True, "message": "已删除"})
    except TaskCard.DoesNotExist:
        return JsonResponse({"ok": True, "message": "任务不存在或已删除"})


# ═══════════════════════════════════════════════════════════════
# 步骤截图服务
# ═══════════════════════════════════════════════════════════════

def serve_step_screenshot(request, filepath):
    """GET /api/runner/step-screenshots/<path:filepath> — Serve annotated step screenshot."""
    full_path = os.path.normpath(os.path.join(str(settings.SCREENSHOT_DIR), filepath))
    # Security: ensure the resolved path is within SCREENSHOT_DIR
    ss_dir = os.path.normpath(str(settings.SCREENSHOT_DIR))
    if not full_path.startswith(ss_dir):
        return JsonResponse({"ok": False, "error": "invalid path"}, status=403)
    if not os.path.isfile(full_path):
        return JsonResponse({"ok": False, "error": "not found"}, status=404)
    return FileResponse(open(full_path, "rb"), content_type="image/png")


# ═══════════════════════════════════════════════════════════════
# TREP v1.0 Phase 0: 监控端点 + 状态快照
# ═══════════════════════════════════════════════════════════════


@require_auth
def run_monitor(request, run_id):
    """GET /api/runner/monitor/:run_id — TREP v1.0 协议健康监控。

    返回: {ok, live, status, device, log_tail, is_running, started_at, ...}
    WS 断开时前端可降级轮询此端点。
    """
    state = get_active_run(run_id)

    if not state:
        # 已完成/不存在的 run → 查 DB
        try:
            record = TestRunRecord.objects.get(run_id=run_id)
            return JsonResponse({
                "ok": True, "run_id": run_id,
                "live": False,
                "status": record.status,
                "device_serial": record.device_serial,
                "selected_cases": record.selected_cases,
                "loop_count": record.loop_count,
                "summary": record.summary,
                "started_at": record.started_at,
                "finished_at": record.finished_at,
            })
        except TestRunRecord.DoesNotExist:
            return JsonResponse({"ok": False, "error": "run not found"}, status=404)

    # Live run — 组装实时状态快照
    adapter = state.adapter
    device_info = {"serial": state.run_model.device_serial, "status": "connected"}
    if adapter and adapter.d:
        try:
            info = adapter.d.info
            device_info.update({
                "resolution": f"{info.get('displayWidth', '?')}x{info.get('displayHeight', '?')}",
                "sdk": info.get("sdkVersion", "?"),
                "battery": info.get("battery", {}).get("level", "?"),
            })
        except Exception:
            device_info["status"] = "disconnected"

    return JsonResponse({
        "ok": True, "run_id": run_id,
        "live": True,
        "status": state.run_model.status.value if hasattr(state.run_model.status, 'value') else str(state.run_model.status),
        "is_running": state.is_running,
        "device": device_info,
        "selected_cases": state.run_model.selected_cases,
        "loop_count": state.run_model.loop_count,
        "started_at": state.run_model.started_at,
        "log_tail": state.log_lines[-50:],
    })


@require_auth
def run_snapshot(request, run_id):
    """GET /api/runner/run/:run_id/snapshot — TREP v1.0 状态快照（WS 降级兜底）。

    返回: {ok, live, status, cases: [{case_id, pass, fail, total}], client_task_id}
    """
    state = get_active_run(run_id)
    client_tid = _run_client_task.get(run_id, "")

    if state:
        # Live run — 从内存组装
        cases = []
        for r in state.all_results:
            cases.append({
                "case_title": r.get("case_title", ""),
                "pass": int(r.get("pass", 0)),
                "fail": int(r.get("fail", 0)),
                "rate": r.get("rate", "0%"),
            })
        return JsonResponse({
            "ok": True, "run_id": run_id,
            "live": True,
            "status": state.run_model.status.value if hasattr(state.run_model.status, 'value') else str(state.run_model.status),
            "cases": cases,
            "client_task_id": client_tid,
        })

    # 已完成 run → 从 DB
    try:
        record = TestRunRecord.objects.get(run_id=run_id)
        from ..models import TestResult as TR
        results = TR.objects.filter(run=record)
        by_case = {}
        for r in results:
            cid = str(r.case_id) if r.case_id else "unknown"
            if cid not in by_case:
                by_case[cid] = {"case_id": cid, "pass": 0, "fail": 0, "total": 0}
            by_case[cid]["total"] += 1
            if r.result == "pass":
                by_case[cid]["pass"] += 1
            else:
                by_case[cid]["fail"] += 1
        return JsonResponse({
            "ok": True, "run_id": run_id,
            "live": False,
            "status": record.status,
            "cases": list(by_case.values()),
            "client_task_id": record.client_task_id,
        })
    except TestRunRecord.DoesNotExist:
        return JsonResponse({"ok": False, "error": "run not found"}, status=404)
