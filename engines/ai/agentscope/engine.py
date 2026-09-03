"""AgentScope 引擎实现 — 把 TaskRequest 装配成三模型工作流并返回归一化 TaskResult。"""

from __future__ import annotations

import asyncio

from engines.ai.base import ModelSpec, TaskRequest, TaskResult

from .config import DeviceExecutionConfig, ModelConfig, PlatformTaskConfig
from .model import DeviceExecution, PlatformTask
from .workflow import DeviceExecutionWorkflow, PlatformTaskWorkflow

__all__ = ["AgentScopeEngine"]


def _to_model_config(spec: ModelSpec) -> ModelConfig:
    """协议 ModelSpec → 引擎内部 ModelConfig（base_url 已由 Django 层解析）。"""
    return ModelConfig(
        provider=spec.provider,
        model_name=spec.model_name,
        api_key=spec.api_key,
        base_url=spec.base_url,
    )


def _workflow_result_to_task_result(result: dict) -> TaskResult:
    """松散 workflow dict → 归一化 TaskResult（两条线路同构）。"""
    ok = result.get("status") == "success"
    completed = result.get("completed") or []
    failed = result.get("failed") or []
    if ok:
        summary = "完成 " + "、".join(completed) if completed else "任务完成"
    else:
        summary = result.get("reason") or result.get("message") or "任务失败"
    return TaskResult(
        status="success" if ok else "fail",
        summary=summary,
        completed=completed,
        failed=failed,
        log=result.get("log") or [],
        usage=result.get("usage") or {},
        reason=result.get("reason") or result.get("message") or "",
    )


class AgentScopeEngine:
    """AgentScope 引擎：阻塞 run()，内部 asyncio.run 跑三模型工作流。"""

    def run(self, req: TaskRequest) -> TaskResult:
        if req.route == "platform_task":
            config = PlatformTaskConfig(
                planner=_to_model_config(req.models["planner"]),
                executor=_to_model_config(req.models["executor"]),
                verifier=_to_model_config(req.models["verifier"]),
                max_loops=req.max_loops,
            )
            pt = PlatformTask(config, tools=req.tools, user_id=req.user_id)
            wf = PlatformTaskWorkflow(pt, serial=req.device_serial)
            result = asyncio.run(
                wf.run(
                    req.goal,
                    requirements=req.requirements,
                    checklist=req.checklist,
                    report_name=req.report_name,
                )
            )
        else:
            config = DeviceExecutionConfig(
                planner=_to_model_config(req.models["planner"]),
                executor=_to_model_config(req.models["executor"]),
                verifier=_to_model_config(req.models["verifier"]),
                max_loops=req.max_loops,
            )
            dev = DeviceExecution(config, tools=req.tools, user_id=req.user_id)
            wf = DeviceExecutionWorkflow(dev, serial=req.device_serial)
            result = asyncio.run(wf.run(req.goal))
        return _workflow_result_to_task_result(result)
