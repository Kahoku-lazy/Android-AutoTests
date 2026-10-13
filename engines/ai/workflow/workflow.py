"""工作流层：编排 planner → SOP，每一步 = 执行者 + 验证者 + 最多驳回 max_loops 次。

本层负责规划取数、数据契约与 JSON→契约解析、平台职责接线（步骤输入前缀、日志开窗读窗、
点击证据、关键词回填、验证截图落盘）、进度推送、过程记录与成败收敛；步骤的推进与驳回计次
交给 `SOPEngine` 驱动 `ExecutionSOPStep`。用量由本层持有的 `UsageAccumulator` 累加总账。
"""

from __future__ import annotations

import json
import logging
import re

from typing import Literal

from agentscope.message import Msg, UserMsg
from agentscope.sop import SOP, SOPEngine, SOPPhase
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from engines.ai.agents import DeviceExecutionConfig, ExecutorRole, PlannerRole, VerifierRole
from engines.ai.base import LogEvidenceProvider
from engines.ai.billing import UsageAccumulator
from engines.ai.messaging import RoleResult

from .evidence import save_verify_screenshot
from .logcheck import (
    build_executor_log_check,
    checked_log_keywords,
    detected_log_timestamp,
    extract_action_time,
)
from .logcheck import (
    render_log_evidence as _render_log_evidence,
)
from .sop_step import ExecutionSOPContext, ExecutionSOPStep

logger = logging.getLogger("ai_assistant.workflow")

# SOP 引擎每步尝试前后产出的自定义事件名
SOP_STEP_STARTED = "SOP_STEP_STARTED"
SOP_STEP_ENDED = "SOP_STEP_ENDED"


# ── 数据契约（节点间交互的数据类型，模型自由文本 → 强类型）──


class Step(BaseModel):
    """单个操作步骤：planner 拆解出的最小执行单元（一个动作 + 其断言）。"""

    model_config = ConfigDict(populate_by_name=True)
    action: str = Field(description="一个操作（一个步骤只一个操作；点击类先找元素再点击）")
    assertion: str = Field(
        alias="assert",
        description="该操作的断言（操作后屏幕上可观察到的期望结果，供 verifier 比对）",
    )
    log_check: bool = Field(
        default=False,
        description="该步断言是否需靠设备日志核对（真时执行侧一并产出 5 秒窗口日志）",
    )

    @field_validator("log_check", mode="before")
    @classmethod
    def _lenient_log_check(cls, value):
        """把模型给出的 log_check 宽松转成布尔；无法识别时返回 False。"""
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y", "on", "是"}
        return False


class Plan(BaseModel):
    """planner 输出：步骤列表（工作流据此逐步执行）。

    模型若额外输出 `goal`，按 pydantic 默认行为忽略，不影响解析。
    """

    steps: list[Step] = Field(description="操作步骤列表")


class ExecutionOutput(BaseModel):
    """executor 输出：执行结果 + 点击前时间戳 + 点击后截图路径。

    `click_timer` / `screenshot` 由模型照抄工具返回；平台不替模型补值，取不到即空串。
    权威点击证据另由平台按工具轨迹装配（见 `logcheck`）。
    """

    result: Literal["PASS", "FAIL"] = Field(description="执行结果")
    click_timer: str = Field(default="", description="点击前的时间戳（无点击时为空串）")
    screenshot: str = Field(default="", description="点击后截图的相对路径（未截图时为空串）")


class VerificationOutput(BaseModel):
    """verifier 输出：验收结论 + 两条时间坐标 + 关键词 + 验证截图 + 实际结果。

    `click_timer` / `logAssertionTimer` 由模型照抄平台下发的输入；`logAssertionInfo`
    由平台按检查工具的调用自动填；`screenshot` 抄本次截图工具返回的路径。取不到一律空串。
    """

    model_config = ConfigDict(populate_by_name=True)
    result: Literal["PASS", "FAIL"] = Field(description="验收结论：PASS=符合断言 FAIL=未达成")
    click_timer: str = Field(default="", description="点击前的时间戳（本步无点击时为空串）")
    log_assertion_timer: str = Field(
        default="",
        alias="logAssertionTimer",
        description="检测到日志关键词的时间戳（未检测到 / 未采集日志时为空串）",
    )
    screenshot: str = Field(default="", description="验证截图的相对路径（未取到路径时为空串）")
    log_assertion_info: str = Field(
        default="",
        alias="logAssertionInfo",
        description="本轮检查的日志关键词（平台按检查工具调用自动填；未检查时为空串）",
    )
    actual: str = Field(default="", description="实际结果（截图里真实看到了什么）")


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
    """组装运行中进度：与终态共用 `WorkflowResult`，status 固定 running。

    Args:
        cfg: 三角色配置（取模型名 + max_loops）。
        usage: 当前累计用量。
        summary: 进度摘要（如「步骤 2/5 验收 True」）。
        plan: 规划结果。
        log: 累计过程记录。
        done: 已完成步骤 action 列表。

    Returns:
        `WorkflowResult.model_dump()`（status=running）。
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


def _step_action_times(result: RoleResult | None) -> list[str]:
    """本步全部副作用动作的发出时刻（去重升序，北京时间毫秒）；无动作返回空列表。

    只需读本步的 `tool_usage`（工具轨迹按轮隔离）。
    """
    if result is None:
        return []
    rows = [
        item
        for item in (result.tool_usage or [])
        if isinstance(item, dict) and item.get("type") == "result"
    ]
    stamps: list[str] = []
    for item in rows:
        raw = item.get("output")
        text = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, default=str)
        stamp = extract_action_time(text)
        if stamp and stamp not in stamps:
            stamps.append(stamp)
    return sorted(stamps)


def _first_action_time(result: RoleResult | None) -> str:
    """本步最早一次副作用动作的发出时刻（单动作场景的便捷入口）。"""
    stamps = _step_action_times(result)
    return stamps[0] if stamps else ""


def _fill_log_assertion(verdict: VerificationOutput, result: RoleResult) -> VerificationOutput:
    """平台按日志检查工具的实际调用回填验收结论的两个日志字段。

    `logAssertionInfo` 取本轮查过的关键词（按调用顺序去重、以「、」连接，覆盖模型自述）；
    `logAssertionTimer` 仅在模型留空且工具确实检测到时补最早命中时间戳，模型已写值不覆盖。
    """
    keywords = checked_log_keywords(result)
    if keywords:
        verdict.log_assertion_info = "、".join(keywords)
    if not verdict.log_assertion_timer.strip():
        stamp = detected_log_timestamp(result)
        if stamp:
            verdict.log_assertion_timer = stamp
    return verdict


def _exec_evidence_text(exec_out: ExecutionOutput) -> str:
    """执行侧证据文本（按执行契约三字段拼装，缺项如实标注）。"""
    click = exec_out.click_timer.strip() or "本步无点击"
    shot = exec_out.screenshot.strip() or "本步未截图"
    return f"点击前时间戳={click}；点击后截图={shot}"


def _log_step(
    step: Step,
    loop: int,
    exec_out: ExecutionOutput,
    verdict: VerificationOutput,
    screenshot: str = "",
    log_evidence: dict | None = None,
    executor_log_check: dict | None = None,
) -> dict:
    """单次步骤尝试的过程记录（不含模型思考与工具明细）。

    Args:
        step: 本步骤（action + 断言）。
        loop: 第几次尝试（1 起）。
        exec_out: 执行结果。
        verdict: 验收结论。
        screenshot: 验收证据截图相对路径（MEDIA），可空。
        log_evidence: 本步的日志证据块（可空）。
        executor_log_check: 执行侧点击证据（可空；无点击且不需日志时不写键）。

    Returns:
        {action, assert, loop, executor, verifier, screenshot?, log_evidence?,
         executor_log_check?}
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
    if log_evidence:
        entry["log_evidence"] = log_evidence
    if executor_log_check and (executor_log_check.get("clicks") or executor_log_check.get("log")):
        entry["executor_log_check"] = executor_log_check
    return entry


def _step_failure(step: Step | None, state) -> dict:
    """失败步骤记录 {action, assert, actual}（actual 取最后一次驳回的说明）。"""
    actual = ""
    verifications = list(getattr(state, "verifications", None) or [])
    if verifications:
        actual = verifications[-1].message or ""
    return {
        "action": getattr(step, "action", "") if step is not None else "",
        "assert": getattr(step, "assertion", "") if step is not None else "",
        "actual": actual,
    }


def _step_index(subject: str) -> int:
    """从步骤标识（「步骤 2/5」）取回步骤序号；取不到返回 0（调用方会跳过）。"""
    found = re.search(r"步骤\s*(\d+)/", str(subject))
    return int(found.group(1)) if found else 0


# ── 工作流 ──


class DeviceExecutionWorkflow:
    """设备执行工作流：planner → SOP，每步「执行 ↔ 验收」最多驳回 max_loops 次。

    三个单角色对象由构造注入；与角色之间只经 `run() → RoleResult` 传递数据。
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
        log_evidence: LogEvidenceProvider | None = None,
        log_keywords: str = "",
        run_state=None,
    ):
        """Args:
        planner: 规划角色对象。
        executor: 执行角色对象。
        verifier: 验收角色对象。
        config: 三角色配置（取 max_loops 与结果 models 元数据；max_loops 即 SOP 的 max_attempts）。
        serial: 目标设备 serial。
        on_progress: 进度回调（可空）。
        task_id: 任务 id（验收截图落盘用）。
        media_root: MEDIA_ROOT 绝对路径；空则跳过落盘。
        log_evidence: 设备日志证据提供者；空则不采集日志证据。
        log_keywords: 当前日志关键词表文本（空 = 不附）。
        run_state: 已保存的运行状态（`SOPRunState`）；给定则续跑，已完成的步骤被跳过。
            步骤数与状态不匹配由 `SOPEngine` 抛 `ValueError`。
        """
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.config = config
        self.serial = serial
        self._on_progress = on_progress
        self._task_id = task_id
        self._media_root = media_root
        self._log_evidence = log_evidence
        self._log_keywords = log_keywords
        self._usage = UsageAccumulator()
        self.run_state = run_state

    # ── 设备日志证据（动作前开窗 → 动作后读窗）──

    def _open_log_window(self, idx: int) -> str:
        """步骤交给执行模型之前开日志窗；无提供者或开窗失败时返回空串。"""
        if self._log_evidence is None:
            return ""
        try:
            window_id = str(self._log_evidence.open_window(self.serial, f"step-{idx}"))
        except Exception as exc:  # 证据缺失不该中断任务，只降级
            logger.warning("【日志窗口】步骤 %d 开窗失败：%s", idx, exc)
            return ""
        logger.info("【日志窗口】步骤 %d 已开窗 id=%s", idx, window_id)
        return window_id

    def _read_log_window(
        self, idx: int, window_id: str, action_times: list[str] | None = None
    ) -> dict | None:
        """动作后读窗取证据；无提供者、无窗口或读窗失败时返回 None。"""
        if self._log_evidence is None or not window_id:
            return None
        stamps = list(action_times or [])
        try:
            evidence = self._log_evidence.read_window(
                self.serial,
                window_id=window_id,
                action_times=stamps,
                wait_seconds=self.config.log_wait_seconds,
            )
        except Exception as exc:  # 同上：日志证据是加分项，不能因它中断任务
            logger.warning("【日志窗口】步骤 %d 读窗失败：%s", idx, exc)
            return None
        logger.info(
            "【日志证据】步骤 %d 动作时间=%s（本步 %d 次）结论=%s 命中=%d 窗口行数=%s",
            idx,
            stamps[0] if stamps else "-",
            len(stamps),
            evidence.get("conclusion"),
            len(evidence.get("hits") or []),
            evidence.get("window_line_count"),
        )
        return evidence if isinstance(evidence, dict) else None

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
            Plan（steps）；模型输出无效返回 None。
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
            result="FAIL",
            click_timer="",
            screenshot="",
        )
        logger.info(
            "【executor 输出】result=%s click_timer=%s screenshot=%s",
            exec_out.result,
            exec_out.click_timer,
            exec_out.screenshot,
        )
        return exec_out, result.screenshot, result

    async def _verify_step(
        self,
        step: Step,
        idx: int,
        total: int,
        exec_out: ExecutionOutput,
        screenshot,
        log_evidence: dict | None = None,
    ) -> tuple[VerificationOutput, object | None, RoleResult]:
        """验收一步：调 verifier 对比断言 + 截图 + 日志证据，返回结论 + 验证侧截图。

        Args:
            step: 本步骤（action + 断言）。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            exec_out: 执行结果（result 与点击前时间戳 / 点击后截图路径供 verifier 参考）。
            screenshot: 执行结果截图（DataBlock，可空）。
            log_evidence: 本步日志证据块（可空 = 无日志证据，验收降级为只看截图）。

        Returns:
            (VerificationOutput, verifier 回复中的截图 DataBlock|None, RoleResult)。
        """
        logger.info(
            "【verifier 输入】步骤%d/%d action=%r assert=%r 日志证据=%s",
            idx,
            total,
            step.action,
            step.assertion,
            "有" if log_evidence else "无",
        )
        result = await self.verifier.run(
            self.serial,
            step.assertion,
            idx,
            total,
            exec_out.result,
            _exec_evidence_text(exec_out),
            screenshot,
            _render_log_evidence(log_evidence),
            self._log_keywords,
        )
        out = self._ingest(result)
        verdict = _coerce(VerificationOutput, out) or VerificationOutput(
            result="FAIL",
            actual="验收模型输出无效",
        )
        verdict = _fill_log_assertion(verdict, result)
        logger.info(
            "【verifier 输出】result=%s 关键词=%s 日志时间=%s actual=%s",
            verdict.result,
            verdict.log_assertion_info or "-",
            verdict.log_assertion_timer or "-",
            verdict.actual,
        )
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

    # ── SOP 编排 ──

    def _step_context(self, step: Step, idx: int, total: int) -> ExecutionSOPContext:
        """本步的平台上下文（平台职责经此注入 SOP 步骤）。"""
        return ExecutionSOPContext(
            index=idx,
            total=total,
            detail=step,
            serial=self.serial,
            execute_step=self._execute_step,
            verify_step=self._verify_step,
            open_window=self._open_log_window,
            close_window=self._read_log_window,
            action_times=_step_action_times,
            build_log_check=build_executor_log_check,
            save_screenshot=lambda idx_, loop_, block: save_verify_screenshot(
                self._media_root, self._task_id, idx_, loop_, block
            ),
            log_keywords=self._log_keywords,
        )

    def _steps(self, plan: Plan) -> list[ExecutionSOPStep]:
        """把规划结果变成一个 SOP 步骤列表（一步 = 一执行者 + 一验证者 + max_loops 次驳回）。"""
        max_attempts = max(1, self.config.max_loops)  # 显式 clamp，杜绝 None 哨兵
        total = len(plan.steps)
        steps: list[ExecutionSOPStep] = []
        for idx, step in enumerate(plan.steps, 1):
            steps.append(
                ExecutionSOPStep(
                    subject=f"步骤 {idx}/{total}",
                    description=step.assertion,
                    context=self._step_context(step, idx, total),
                    max_attempts=max_attempts,
                )
            )
        return steps

    def _prepare(self, steps: list[ExecutionSOPStep], plan: Plan) -> None:
        """每步开始前：刷新平台上下文与产出槽、清角色上下文、记用量基线。"""
        total = len(plan.steps)
        for idx, (step, detail) in enumerate(zip(steps, plan.steps), 1):
            step.prepare(self._step_context(detail, idx, total))
            step.sink.usage_before = self._usage.as_dict()
            self.executor.reset_context()
            self.verifier.reset_context()

    async def _drive(
        self,
        engine: SOPEngine,
        plan: Plan,
        log: list[dict],
        done: list[str],
    ) -> None:
        """驱动 SOP：消费事件流，把步骤开始与尝试结束接进进度口径与用量日志。"""
        steps = list(engine.sop.steps)
        # 执行侧输入前缀由角色自己拼，这里只给一句任务目标
        async for event in engine.reply_stream(UserMsg(name="user", content="执行设备任务步骤")):
            if isinstance(event, Msg):
                continue
            name = getattr(event, "name", "")
            value = getattr(event, "value", None) or {}
            if name == SOP_STEP_STARTED:
                logger.info(
                    "【② %s】SOP 步骤开始（第 %s 次尝试）",
                    value.get("step", ""),
                    value.get("attempt", ""),
                )
            elif name == SOP_STEP_ENDED:
                idx = _step_index(value.get("step", ""))
                self._after_attempt(engine, steps, idx, plan, log, done)

    def _after_attempt(
        self,
        engine: SOPEngine,
        steps: list[ExecutionSOPStep],
        idx: int,
        plan: Plan,
        log: list[dict],
        done: list[str],
    ) -> None:
        """一次尝试结束后：写过程记录 + 推进度 + 打印本步 token 增量。"""
        if idx < 1 or idx > len(steps):
            return
        step = steps[idx - 1]
        sink = step.sink
        loop = len(engine.state.steps[idx - 1].verifications)  # 每轮尝试记一条结论
        if sink.exec_out is None or sink.verdict is None:
            # 交付或结论缺失：本轮无过程记录可写
            sink.reset(loop + 1)
            return
        log.append(
            _log_step(
                plan.steps[idx - 1],
                loop,
                sink.exec_out,
                sink.verdict,
                sink.screenshot,
                sink.log_evidence,
                sink.executor_log_check,
            )
        )
        self._report(
            f"步骤 {idx}/{len(steps)} 验收 {sink.verdict.result}",
            plan,
            log,
            done,
        )
        self._log_step_usage(idx, len(steps), sink.usage_before or self._usage.as_dict())
        sink.reset(loop + 1)

    async def run(self, user_input: str) -> dict:
        """入口编排：规划 → SOP 逐步（执行 ↔ 验收）→ 成败收敛。

        Args:
            user_input: 用户一句话 UI 操作需求。

        Returns:
            `WorkflowResult.model_dump()`（终态 dict）。
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

        # ① 规划：planner 出 Plan（steps）
        plan = await self._plan(user_input)
        if plan is None or not plan.steps:
            logger.error("【工作流】规划模型未产出步骤 → 任务失败")
            return self._fail("规划模型未产出步骤", None, [])

        done: list[str] = []
        log: list[dict] = []
        self._report(f"已规划 {len(plan.steps)} 个步骤", plan, log, done)

        # ② SOP：每步先清角色上下文 → 执行 ↔ 验收（驳回计次由框架负责）→ 通过才勾选
        steps = self._steps(plan)
        self._prepare(steps, plan)
        engine = SOPEngine(
            SOP(name="device-execution", steps=steps, description=user_input),
            state=self.run_state,
        )
        self.run_state = engine.state
        await self._drive(engine, plan, log, done)

        # ③ 收敛：全部步骤通过 → success；否则整轮失败（失败步骤给出驳回说明）
        records = list(engine.state.steps)
        for idx, record in enumerate(records, 1):
            if record.phase is SOPPhase.COMPLETED:
                done.append(plan.steps[idx - 1].action)
                continue
            step = plan.steps[idx - 1]
            logger.error("【② 步骤 %d】未通过 → 任务失败", idx)
            self._log_final_usage()
            return self._fail(
                f"步骤未通过：{step.action}",
                plan,
                log,
                failed=[_step_failure(step, record)],
            )

        logger.info(
            "【工作流结束】全部步骤通过，completed=%s",
            json.dumps(done, ensure_ascii=False),
        )
        self._log_final_usage()
        return self._success(plan, done, log)
