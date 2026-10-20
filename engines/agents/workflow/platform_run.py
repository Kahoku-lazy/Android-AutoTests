"""
python -m 调试路径: engines.agents.workflow.platform_run

本模块的业务功能如下：
1. run_platform_sop: 平台启动 SOP。校验 YAML，按序跑用例，不接收工具清单。
2. request_cancel: 取消正在跑的 SOP 事件流。
"""

from __future__ import annotations

import asyncio
import inspect
import threading

from collections.abc import Callable
from pathlib import Path

from engines.agents.prompt_config import EXECUTOR_PROMPT
from engines.agents.prompts.verifier_prompt import verifier_system_prompt
from engines.agents.role.base import AgentRoleConfig, BaseRole
from engines.agents.role.config import ModelConfig
from engines.agents.tools_config import build_executor_toolkit, build_verifier_toolkit
from engines.agents.workflow.case_file import LOAD_FAIL, LOAD_OK, validate_platform_yaml
from engines.agents.workflow.ui_auto_workflow import AgentSOPWorkflow

_cancel_events: dict[int, threading.Event] = {}
_inflight: dict[int, tuple[asyncio.AbstractEventLoop, asyncio.Task]] = {}

CaseRunner = Callable[[str, list[tuple[str, str]], str], str]


def bind_cancel(task_id: int) -> threading.Event:
    """为一次平台任务登记取消信号。"""
    event = threading.Event()
    _cancel_events[task_id] = event
    return event


def request_cancel(task_id: int) -> None:
    """取消正在跑的 SOP 事件流。不调用角色基类的中断方法。"""
    event = _cancel_events.get(task_id)
    if event is not None:
        event.set()
    pair = _inflight.get(task_id)
    if pair is None:
        return
    loop, task = pair
    if loop.is_running():
        loop.call_soon_threadsafe(task.cancel)


def clear_cancel(task_id: int) -> None:
    """任务结束后丢掉取消登记。"""
    _cancel_events.pop(task_id, None)
    _inflight.pop(task_id, None)


def run_platform_sop(
    yaml_path: str,
    opening: str,
    *,
    executor_model: ModelConfig,
    verifier_model: ModelConfig,
    task_id: int = 0,
    case_title: str = "",
    run_case: CaseRunner | None = None,
) -> dict:
    """按 YAML 跑 SOP。工具由引擎代码装配，本函数不接收工具清单。

    Args:
        yaml_path: YAML 文件路径。
        opening: 开场说明。
        executor_model: 后端注入的执行模型。
        verifier_model: 后端注入的验收模型。
        task_id: 平台任务 id。0 表示不登记取消。
        case_title: 只跑该标题的用例；空串表示按文件顺序跑全部。
        run_case: 替身。省略时用注入的模型与代码中的工具包跑真 SOP。

    Returns:
        load_message、reason、status、completed。
    """
    path = Path(yaml_path)
    if not path.is_file():
        return _fail("YAML 文件不存在")
    cases, reason = validate_platform_yaml(path.read_text(encoding="utf-8"))
    if reason:
        return _fail(reason)
    wanted = str(case_title or "").strip()
    if wanted:
        cases = [case for case in cases if case.title == wanted]
        if not cases:
            return {
                "load_message": LOAD_OK,
                "reason": f"用例「{wanted}」不存在",
                "status": "fail",
                "completed": [],
            }
    cancel_event = _cancel_events.get(task_id)
    if run_case is not None:
        return _drive_stub(cases, opening, run_case, cancel_event)
    return asyncio.run(
        _drive_real(cases, opening, executor_model, verifier_model, task_id, cancel_event)
    )


def _drive_stub(cases, opening: str, run_case: CaseRunner, cancel_event) -> dict:
    completed: list[str] = []
    for case in cases:
        if cancel_event is not None and cancel_event.is_set():
            return _cancelled(completed)
        steps = [(step.action, step.expected) for step in case.steps]
        phase = run_case(case.title, steps, opening)
        if phase == "cancelled":
            return _cancelled(completed)
        if phase != "completed":
            return {
                "load_message": LOAD_OK,
                "reason": f"用例「{case.title}」未完成",
                "status": "fail",
                "completed": completed,
            }
        completed.append(case.title)
    return {
        "load_message": LOAD_OK,
        "reason": "",
        "status": "success",
        "completed": completed,
    }


async def _drive_real(
    cases, opening, executor_model, verifier_model, task_id, cancel_event
) -> dict:
    current = asyncio.current_task()
    if task_id and current is not None:
        _inflight[task_id] = (asyncio.get_running_loop(), current)
    executor = _build_role(
        executor_model,
        name="executor_role",
        system_prompt=EXECUTOR_PROMPT,
        toolkit=build_executor_toolkit(),
    )
    verifier = _build_role(
        verifier_model,
        name="verifier_role",
        system_prompt=verifier_system_prompt(),
        toolkit=build_verifier_toolkit(),
    )
    workflow = AgentSOPWorkflow(executor.agent, verifier.agent)
    completed: list[str] = []
    try:
        for case in cases:
            if cancel_event is not None and cancel_event.is_set():
                return _cancelled(completed)
            steps = [(step.action, step.expected) for step in case.steps]
            phase = await workflow.run_workflow(case.title, steps, opening)
            if phase != "completed":
                return {
                    "load_message": LOAD_OK,
                    "reason": f"用例「{case.title}」未完成",
                    "status": "fail",
                    "completed": completed,
                }
            completed.append(case.title)
        return {
            "load_message": LOAD_OK,
            "reason": "",
            "status": "success",
            "completed": completed,
        }
    except asyncio.CancelledError:
        return _cancelled(completed)
    finally:
        _inflight.pop(task_id, None)


def _build_role(model: ModelConfig, *, name: str, system_prompt: str, toolkit) -> BaseRole:
    secret = model.api_key
    api_key = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    return BaseRole(
        *AgentRoleConfig(
            provider=model.provider,
            model_name=model.model_name,
            base_url=model.base_url,
            api_key=api_key,
            name=name,
            system_prompt=system_prompt,
            toolkit=toolkit,
            vision=True,
        ).load_config()
    )


def _fail(reason: str) -> dict:
    return {
        "load_message": LOAD_FAIL,
        "reason": reason,
        "status": "fail",
        "completed": [],
    }


def _cancelled(completed: list[str]) -> dict:
    return {
        "load_message": LOAD_OK,
        "reason": "用户关闭",
        "status": "cancelled",
        "completed": completed,
    }


def platform_entry_accepts_tools() -> bool:
    """供测试确认入口参数里没有工具清单。"""
    return "tools" in inspect.signature(run_platform_sop).parameters
