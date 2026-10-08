"""AgentScope 引擎组合根 —— 把 TaskRequest 装配成设备执行工作流，返回归一化 TaskResult。

五部分的唯一组合点：智能体（agents，含 tools 的装配）→ 工作流（workflow）；
费用计算（billing）由智能体侧算本轮、工作流侧累总账。协议与注册表在本层。
"""

from __future__ import annotations

import asyncio

from engines.ai.agents import DeviceExecutionConfig, ModelConfig, build_device_models
from engines.ai.base import ModelSpec, TaskRequest, TaskResult
from engines.ai.workflow import DeviceExecutionWorkflow

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
            config,
            req.tools,
            req.user_id,
            skill_dirs=req.skill_dirs,
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
            log_evidence=req.log_evidence,
            log_keywords=req.log_keywords,
        )
        result = asyncio.run(wf.run(req.goal))
        return _workflow_result_to_task_result(result)
