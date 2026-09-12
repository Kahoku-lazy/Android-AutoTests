"""工作流层：编排 planner → executor ↔ verifier 流程。

职责边界（面向对象）：
- 工作流【只做编排 + 数据契约 + JSON→契约解析】，不碰 AgentScope（零框架依赖）。
- 模型交互（拼 prompt + 调角色 + 回复解析）已下沉 model.py 的单角色；
  每个角色 run() 返回 RoleResult（输出/思考/工具/上下文/本轮用量/费用）。
- 用量累计：工作流持有 UsageAccumulator，按模型自报 usage 累加总账。
"""

from __future__ import annotations

import json
import logging
import re

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import DeviceExecutionConfig
from .evidence import save_verify_screenshot
from .model import ExecutorRole, PlannerRole, RoleResult, VerifierRole
from .usage import UsageAccumulator

logger = logging.getLogger("ai_assistant.workflow")


# ── 数据契约（节点间交互的数据类型，模型自由文本 → 强类型）──


class Step(BaseModel):
    """单个操作步骤：planner 拆解出的最小执行单元（一个动作 + 其断言）。"""

    model_config = ConfigDict(populate_by_name=True)
    action: str = Field(description="一个操作（一个步骤只一个操作；点击类先找元素再点击）")
    assertion: str = Field(
        alias="assert",
        description="该操作的断言（操作后屏幕上可观察到的期望结果，供 verifier 比对）",
    )


class Plan(BaseModel):
    """planner 输出：总目标 + 步骤列表（工作流据此逐步骤执行）。"""

    goal: str = Field(default="", description="一句话总目标")
    steps: list[Step] = Field(description="操作步骤列表")


class ExecutionOutput(BaseModel):
    """executor 输出：执行结果（action + PASS/FAIL + 说明）。"""

    action: str = Field(description="执行的操作")
    result: Literal["PASS", "FAIL"] = Field(description="执行结果")
    message: str = Field(description="操作说明或遇到的问题")


class VerificationOutput(BaseModel):
    """verifier 输出：验收结论（断言 vs 实际 + 是否通过）。"""

    model_config = ConfigDict(populate_by_name=True)
    action: str = Field(description="被验证的操作")
    assertion: str = Field(alias="assert", description="断言（期望结果）")
    actual: str = Field(description="实际结果（截图里真实看到了什么）")
    result: bool = Field(description="最终结论：true=通过 false=未通过")


class WorkflowResult(BaseModel):
    """工作流终态结果（运行中进度与终态共用，用 status 区分 running/success/fail）。"""

    status: Literal["running", "success", "fail"] = Field(description="运行态/成功/失败")
    summary: str = Field(default="", description="一句话摘要（前端首行展示）")
    reason: str = Field(default="", description="失败原因（成功为空）")
    completed: list[str] = Field(default_factory=list, description="已完成步骤的 action 列表")
    failed: list[dict] = Field(
        default_factory=list,
        description="失败步骤 [{action, assert, actual}]",
    )
    plans: list[dict] = Field(default_factory=list, description="规划结果（Plan.model_dump）")
    log: list[dict] = Field(default_factory=list, description="逐步骤过程记录（详情页渲染）")
    usage: dict = Field(
        default_factory=dict,
        description="任务级 token 用量（含 models / by_role 拆分）",
    )
    models: dict = Field(default_factory=dict, description="三角色模型名 + max_loops")
    max_loops: int = Field(default=0, description="每步最大重试次数")


# ── JSON 解析辅助 ──


def _parse_json(text: str) -> dict | None:
    """从模型自由文本里提取 JSON 对象（容忍 markdown 代码块与前后缀文字）。

    Args:
        text: 模型输出文本。

    Returns:
        解析出的 dict；非 JSON / 提取失败返回 None。
    """
    if not text:
        return None
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", s, re.DOTALL)
    if m:
        s = m.group(1)
    else:
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        s = s[start : end + 1]
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def _coerce(model_cls, obj):
    """Pydantic 建模兜底：非 dict / 校验失败返回 None，由调用方走失败分支。

    Args:
        model_cls: 目标契约类（Plan/ExecutionOutput/VerificationOutput）。
        obj: 待建模的 dict。

    Returns:
        建模成功的实例；失败返回 None（模型输出无效）。
    """
    if not isinstance(obj, dict):
        return None
    try:
        return model_cls(**obj)
    except ValidationError:
        return None


# ── 进度 / 结果组装 ──


def _cfg_models(cfg) -> dict:
    """从配置抽取结果里的 models 元数据（三角色模型名 + max_loops）。"""
    return {
        "planner": cfg.planner.model_name,
        "executor": cfg.executor.model_name,
        "verifier": cfg.verifier.model_name,
        "max_loops": cfg.max_loops,
    }


def _progress_payload(
    cfg,
    usage,
    *,
    summary: str,
    plan: Plan,
    log: list[dict],
    done: list[str],
) -> dict:
    """运行中检查点：与终态共用 WorkflowResult，status 固定 running。

    Args:
        cfg: 三角色配置（取模型名 + max_loops）。
        usage: 当前累计用量。
        summary: 进度摘要（如「步骤 2/5 验收 True」）。
        plan: 规划结果。
        log: 累计过程记录。
        done: 已完成步骤 action 列表。

    Returns:
        WorkflowResult.model_dump()（status=running）。
    """
    return WorkflowResult(
        status="running",
        summary=summary,
        completed=list(done),
        plans=[plan.model_dump(by_alias=True)],
        log=log,
        usage=usage,
        models=_cfg_models(cfg),
        max_loops=cfg.max_loops,
    ).model_dump()


def _emit_progress(on_progress, payload: dict) -> None:
    """安全触发进度回调（回调异常不阻断主流程）。"""
    if not on_progress:
        return
    try:
        on_progress(payload)
    except Exception:
        logger.exception("task progress callback failed")


_TRACE_THINK_MAX = 2000
_TRACE_THINK_N = 24
_TRACE_TOOL_N = 80
_TRACE_INPUT_MAX = 800
_TRACE_TEXT_MAX = 4000
_TRACE_OUTPUT_MAX = 800


def _clip_json(value, limit: int = _TRACE_INPUT_MAX) -> str:
    """工具入参 → 短文本（截断，避免把截图/长 JSON 写入任务 log）。"""
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        text = str(value)
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def _clip_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def _role_trace(result: RoleResult | None) -> dict:
    """从 RoleResult 抽出详情页 Agent Info：输入 / 思考 / 工具 / 文本（无 base64）。"""
    if result is None:
        return {}
    thinking: list[str] = []
    for raw in result.thinking[:_TRACE_THINK_N]:
        text = _clip_text(raw, _TRACE_THINK_MAX)
        if text:
            thinking.append(text)
    tools: list[dict] = []
    for item in result.tool_usage[:_TRACE_TOOL_N]:
        kind = str(item.get("type") or "")
        row: dict = {"type": kind, "name": str(item.get("name") or "")}
        state = item.get("state")
        if state:
            row["state"] = str(state)[:80]
        media_type = item.get("media_type")
        if media_type:
            row["media_type"] = str(media_type)
        if "input" in item and item.get("input") is not None:
            row["input"] = _clip_json(item.get("input"))
        output = item.get("output")
        if output:
            row["output"] = _clip_text(str(output), _TRACE_OUTPUT_MAX)
        shot = str(item.get("screenshot_path") or "").replace("\\", "/").strip()
        if shot:
            row["screenshot_path"] = shot
        tools.append(row)
    out: dict = {}
    input_text = _clip_text(getattr(result, "input_text", "") or "", _TRACE_TEXT_MAX)
    if input_text:
        out["input"] = input_text
    if thinking:
        out["thinking"] = thinking
    if tools:
        out["tools"] = tools
    text = _clip_text(result.output or "", _TRACE_TEXT_MAX)
    if text:
        out["text"] = text
    return out


def _log_step(
    step: Step,
    loop: int,
    exec_out: ExecutionOutput,
    verdict: VerificationOutput,
    screenshot: str = "",
    executor_trace: dict | None = None,
    verifier_trace: dict | None = None,
) -> dict:
    """单次步骤重试的过程记录（详情页逐步骤渲染）。

    Args:
        step: 本步骤（action + 断言）。
        loop: 第几次重试（1 起）。
        exec_out: 执行结果。
        verdict: 验收结论。
        screenshot: 验收证据截图相对路径（MEDIA），可空。
        executor_trace: 执行侧思考 + 工具调用（可空）。
        verifier_trace: 验收侧思考 + 工具调用（可空）。

    Returns:
        {action, assert, loop, executor, verifier, screenshot?, *_trace?}
    """
    entry = {
        "action": step.action,
        "assert": step.assertion,
        "loop": loop,
        "executor": exec_out.model_dump(),
        "verifier": verdict.model_dump(by_alias=True),
    }
    if screenshot:
        entry["screenshot"] = screenshot
    if executor_trace:
        entry["executor_trace"] = executor_trace
    if verifier_trace:
        entry["verifier_trace"] = verifier_trace
    return entry


# ── 工作流 ──


class DeviceExecutionWorkflow:
    """设备执行工作流：planner → executor ↔ verifier 循环。

    对象协作：工作流【组合】三个单角色模型对象（构造注入），不继承、不共享可变状态；
    与角色之间只靠 run()→RoleResult 的消息传递协作。只做编排与数据解析。
    """

    def __init__(
        self,
        planner: PlannerRole,
        executor: ExecutorRole,
        verifier: VerifierRole,
        config: DeviceExecutionConfig,
        serial: str = "",
        on_progress=None,
        task_id: int = 0,
        media_root: str = "",
    ):
        """Args:
        planner/executor/verifier: 三个角色对象（由 build_device_models 创建）。
        config: 三角色配置（取 max_loops + 结果 models 元数据）。
        serial: 目标设备 serial。
        on_progress: 进度回调（可选，运行中检查点推送）。
        task_id: 任务 id（验收截图落盘用）。
        media_root: MEDIA_ROOT 绝对路径；空则跳过落盘。
        """
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.config = config
        self.serial = serial
        self._on_progress = on_progress
        self._task_id = task_id
        self._media_root = media_root
        self._usage = UsageAccumulator()

    # ── 收一轮模型结果（累账 + 解析）──

    def _ingest(self, result: RoleResult) -> dict | None:
        """收一轮模型结果：按模型自报用量累账 + 解析输出 JSON。

        Args:
            result: 角色返回的 RoleResult（含 role/model_name/usage/output）。

        Returns:
            output 解析出的 dict；解析失败返回 None。
        """
        self._usage.acc(result.usage, result.model_name, result.role)
        return _parse_json(result.output)

    # ── 三角色（调模型 + 建模差异）──

    async def _plan(self, user_input: str) -> Plan | None:
        """规划：调 planner 出 Plan；失败返回 None。

        Args:
            user_input: 用户一句话 UI 操作需求。

        Returns:
            Plan（goal + steps）；模型输出无效返回 None。
        """
        logger.info("【① planner 输入】user_input=%r", user_input)
        result = await self.planner.run(user_input)
        out = self._ingest(result)
        plan = _coerce(Plan, (out or {}).get("plan"))
        if plan is None:
            logger.warning(
                "【① planner 输出】未返回有效 JSON，原文=%s",
                result.output,
            )
            return None
        logger.info(
            "【① planner 输出】plan=%s",
            json.dumps(plan.model_dump(by_alias=True), ensure_ascii=False),
        )
        return plan

    async def _execute_step(
        self,
        step: Step,
        idx: int,
        total: int,
        retry_hint: str = "",
    ) -> tuple[ExecutionOutput, object, RoleResult]:
        """执行一步：调 executor 在设备上操作，返回执行结果 + 结果截图。

        Args:
            step: 本步骤（action + 断言）。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            retry_hint: 上次验收失败回灌的修正提示（空串 = 首次执行）。

        Returns:
            (ExecutionOutput, 截图 DataBlock|None, RoleResult)。
        """
        logger.info(
            "【executor 输入】步骤%d/%d action=%r retry_hint=%s",
            idx,
            total,
            step.action,
            retry_hint,
        )
        result = await self.executor.run(self.serial, step.action, idx, total, retry_hint)
        out = self._ingest(result)
        exec_out = _coerce(ExecutionOutput, out) or ExecutionOutput(
            action=step.action,
            result="FAIL",
            message="执行模型输出无效",
        )
        logger.info(
            "【executor 输出】result=%s message=%s",
            exec_out.result,
            exec_out.message,
        )
        return exec_out, result.screenshot, result

    async def _verify_step(
        self,
        step: Step,
        idx: int,
        total: int,
        exec_out: ExecutionOutput,
        screenshot,
    ) -> tuple[VerificationOutput, object | None, RoleResult]:
        """验收一步：调 verifier 对比断言与截图，返回结论 + 验证侧截图。

        Args:
            step: 本步骤（action + 断言）。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            exec_out: 执行结果（result/message 供 verifier 参考）。
            screenshot: 执行结果截图（DataBlock，可空）。

        Returns:
            (VerificationOutput, verifier 回复中的截图 DataBlock|None, RoleResult)。
        """
        logger.info(
            "【verifier 输入】步骤%d/%d action=%r assert=%r",
            idx,
            total,
            step.action,
            step.assertion,
        )
        result = await self.verifier.run(
            self.serial,
            step.assertion,
            idx,
            total,
            exec_out.result,
            exec_out.message,
            screenshot,
        )
        out = self._ingest(result)
        verdict = _coerce(VerificationOutput, out) or VerificationOutput(
            action=step.action,
            assertion=step.assertion,
            actual="验收模型输出无效",
            result=False,
        )
        logger.info("【verifier 输出】result=%s actual=%s", verdict.result, verdict.actual)
        return verdict, result.screenshot, result

    # ── 进度 / 结果辅助 ──

    def _report(self, summary: str, plan: Plan, log: list[dict], done: list[str]) -> None:
        """推送一次运行中进度（若配置了 on_progress）。"""
        _emit_progress(
            self._on_progress,
            _progress_payload(
                self.config,
                self._usage.as_dict(),
                summary=summary,
                plan=plan,
                log=log,
                done=done,
            ),
        )

    def _result(
        self,
        status: str,
        *,
        summary: str = "",
        reason: str = "",
        completed: list[str] | None = None,
        failed: list[dict] | None = None,
        plans: list[dict] | None = None,
        log: list[dict] | None = None,
    ) -> dict:
        """组装终态 WorkflowResult（与进度共用同一模型）。"""
        return WorkflowResult(
            status=status,
            summary=summary,
            reason=reason,
            completed=completed or [],
            failed=failed or [],
            plans=plans or [],
            log=log or [],
            usage=self._usage.as_dict(),
            models=_cfg_models(self.config),
            max_loops=self.config.max_loops,
        ).model_dump()

    def _success(self, plan: Plan, done: list[str], log: list[dict]) -> dict:
        """组装成功终态。"""
        summary = "完成 " + "、".join(done) if done else "任务完成"
        return self._result(
            "success",
            summary=summary,
            completed=done,
            plans=[plan.model_dump(by_alias=True)],
            log=log,
        )

    def _fail(
        self,
        reason: str,
        plan: Plan | None,
        log: list[dict],
        failed: list[dict] | None = None,
    ) -> dict:
        """组装失败终态。"""
        return self._result(
            "fail",
            summary=reason,
            reason=reason,
            failed=failed or [],
            plans=[plan.model_dump(by_alias=True)] if plan else [],
            log=log,
        )

    def _role_delta(self, prev_by_role: dict) -> str:
        """按角色 token 增量 → 一行日志文本（executor/verifier/planner）。"""
        parts = []
        for role in ("executor", "verifier", "planner"):
            b = prev_by_role.get(role, {})
            a = self._usage.by_role.get(role, {})
            din = a.get("input_tokens", 0) - b.get("input_tokens", 0)
            dout = a.get("output_tokens", 0) - b.get("output_tokens", 0)
            if din or dout:
                parts.append(f"{role}: 输入+{din}/输出+{dout}")
        return " · ".join(parts)

    def _log_step_usage(self, idx: int, total: int, before: dict) -> None:
        """打印单步 token 增量（总量 + 按角色）。"""
        logger.info(
            "【token】步骤 %d/%d 消耗：输入 +%d（累计 %d）· 输出 +%d（累计 %d）· 缓存命中 +%d",
            idx,
            total,
            self._usage.input_tokens - before["input_tokens"],
            self._usage.input_tokens,
            self._usage.output_tokens - before["output_tokens"],
            self._usage.output_tokens,
            self._usage.cache_input_tokens - before["cache_input_tokens"],
        )
        logger.info(
            "【token】步骤 %d/%d 按角色：%s",
            idx,
            total,
            self._role_delta(before["by_role"]),
        )

    def _log_final_usage(self) -> None:
        """打印任务级 token 汇总（按模型 + 按角色）。"""
        logger.info(
            "【token 汇总】按模型=%s",
            json.dumps(self._usage.models, ensure_ascii=False),
        )
        logger.info(
            "【token 汇总】按角色=%s",
            json.dumps(self._usage.by_role, ensure_ascii=False),
        )

    # ── 编排 ──

    async def _run_step(
        self,
        step: Step,
        idx: int,
        total: int,
        plan: Plan,
        log: list[dict],
        done: list[str],
    ) -> VerificationOutput | None:
        """单步「执行 → 验收」重试循环；每轮推进 log 并推送进度。

        Args:
            step: 本步骤。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            plan: 规划结果（供进度 payload 用）。
            log: 累计过程记录（本步每轮追加）。
            done: 已完成步骤 action 列表（供进度 payload 用）。

        Returns:
            最终 verdict（通过即返回；耗尽重试返回最后一次未通过的 verdict）。
        """
        max_loops = max(1, self.config.max_loops)  # 显式 clamp，杜绝 None 哨兵
        retry_hint = ""
        verdict: VerificationOutput | None = None
        for loop in range(max_loops):
            logger.info(
                "【② 步骤 %d/%d 重试 %d/%d】开始",
                idx,
                total,
                loop + 1,
                max_loops,
            )
            # 执行 → 验收；证据路径优先用 verifier 工具回传的真实落盘路径
            exec_out, screenshot, exec_role = await self._execute_step(
                step, idx, total, retry_hint
            )
            verdict, verifier_shot, ver_role = await self._verify_step(
                step, idx, total, exec_out, screenshot
            )
            shot_rel = (ver_role.screenshot_path or "").strip()
            if not shot_rel:
                # 回退：从 DataBlock 再落一份 ai_tasks/ 证据（旧链路 / 无路径 summary）
                evidence = verifier_shot if verifier_shot is not None else screenshot
                shot_rel = save_verify_screenshot(
                    self._media_root, self._task_id, idx, loop + 1, evidence
                )
            log.append(
                _log_step(
                    step,
                    loop + 1,
                    exec_out,
                    verdict,
                    shot_rel,
                    _role_trace(exec_role),
                    _role_trace(ver_role),
                )
            )
            self._report(f"步骤 {idx}/{total} 验收 {verdict.result}", plan, log, done)
            if verdict.result is True:
                logger.info("【② 步骤 %d】验收 true → 勾选完成，进入下一步", idx)
                return verdict
            # 验收失败 → 把 actual 回灌给 executor 重试本步
            retry_hint = verdict.actual
            logger.warning(
                "【② 步骤 %d 重试 %d】验收 false → 回灌 actual=%s 重试该步",
                idx,
                loop + 1,
                verdict.actual,
            )
        return verdict

    async def run(self, user_input: str) -> dict:
        """入口编排：规划 → 逐步骤（执行↔验收重试）→ 成败收敛。

        Args:
            user_input: 用户一句话 UI 操作需求。

        Returns:
            WorkflowResult.model_dump()（终态 dict，与进度同构）。
        """
        cfg = self.config
        logger.info("=" * 60)
        logger.info(
            "【工作流开始】user_input=%r | planner=%s executor=%s verifier=%s max_loops=%d",
            user_input,
            cfg.planner.model_name,
            cfg.executor.model_name,
            cfg.verifier.model_name,
            cfg.max_loops,
        )

        # ① 规划：planner 出 Plan（goal + steps）
        plan = await self._plan(user_input)
        if plan is None or not plan.steps:
            logger.error("【工作流】规划模型未产出步骤 → 任务失败")
            return self._fail("规划模型未产出步骤", None, [])

        done: list[str] = []
        log: list[dict] = []
        self._report(f"已规划 {len(plan.steps)} 个步骤", plan, log, done)

        # ② 逐步骤执行：每步先清上下文 → 执行↔验收重试 → 通过才勾选
        for idx, step in enumerate(plan.steps, 1):
            self.executor.reset_context()
            self.verifier.reset_context()
            before = self._usage.as_dict()
            verdict = await self._run_step(step, idx, len(plan.steps), plan, log, done)
            self._log_step_usage(idx, len(plan.steps), before)
            if verdict is None or verdict.result is not True:
                logger.error("【② 步骤 %d】未通过 → 任务失败", idx)
                self._log_final_usage()
                return self._fail(
                    f"步骤未通过：{step.action}",
                    plan,
                    log,
                    failed=[
                        {
                            "action": step.action,
                            "assert": step.assertion,
                            "actual": verdict.actual if verdict else "",
                        }
                    ],
                )
            done.append(step.action)

        # ③ 收敛：全部步骤通过 → success
        logger.info(
            "【工作流结束】全部步骤通过，completed=%s",
            json.dumps(done, ensure_ascii=False),
        )
        self._log_final_usage()
        return self._success(plan, done, log)
