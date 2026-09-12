"""AgentScope 引擎实现 — 把 TaskRequest 装配成设备执行工作流并返回归一化 TaskResult。"""

from __future__ import annotations

import asyncio

from engines.ai.base import ModelSpec, TaskRequest, TaskResult

from .config import DeviceExecutionConfig, ModelConfig
from .model import build_device_models
from .workflow import DeviceExecutionWorkflow

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
    """松散 workflow dict → 归一化 TaskResult。"""
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
        plans=result.get("plans") or [],
        log=result.get("log") or [],
        usage=result.get("usage") or {},
        models=result.get("models") or {},
        reason=result.get("reason") or result.get("message") or "",
    )


class AgentScopeEngine:
    """AgentScope 引擎：阻塞 run()，内部 asyncio.run 跑设备执行工作流。"""

    def run(self, req: TaskRequest) -> TaskResult:
        config = DeviceExecutionConfig(
            planner=_to_model_config(req.models["planner"]),
            executor=_to_model_config(req.models["executor"]),
            verifier=_to_model_config(req.models["verifier"]),
            max_loops=req.max_loops,
        )
        planner, executor, verifier = build_device_models(
            config, req.tools, req.user_id, skill_dirs=req.skill_dirs
        )
        wf = DeviceExecutionWorkflow(
            planner,
            executor,
            verifier,
            config,
            serial=req.device_serial,
            on_progress=req.on_progress,
            task_id=req.task_id,
            media_root=req.media_root,
        )
        result = asyncio.run(wf.run(req.goal))
        return _workflow_result_to_task_result(result)
