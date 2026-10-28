"""
python -m 调试路径: engines.agents.workflow.case_authoring_workflow

本模块的业务功能如下：
1. ModuleOutcome: 一个模块的验收结果（键、名称、行区间、是否通过、是否截断）。
2. CaseAuthoringResult: 一次用例编写运行的阶段、交付文档、历次判决与模块清单。
3. CaseAuthoringWorkflow: 单个模块内「编写角色写文档、验收角色判卷」，驳回后重写。
4. run_case_authoring_modules: 先规划模块，再逐块编写/验收，截断时继续拆分并拼装文档。
5. run_case_authoring: 同步装配并跑完一次模块化用例编写。
"""

from __future__ import annotations

import asyncio
import os

from collections.abc import AsyncGenerator
from dataclasses import dataclass

from agentscope.agent import Agent
from agentscope.message import UserMsg
from agentscope.sop import SOP, SOPEngine, SOPStep, SOPStepRunState

from engines.agents.event_log import write_line
from engines.agents.event_sink import set_case_title
from engines.agents.role.case_roles import build_case_verifier, build_case_writer
from engines.agents.tools.tool_case_module_store import ModuleStore
from engines.agents.workflow.case_goal_workflow import run_goal_module
from engines.agents.workflow.case_module_plan import (
    ModuleRange,
    build_module_document,
    plan_case_modules,
    split_module,
)
from engines.agents.workflow.ui_auto_workflow import show_event

CASE_STEP_SUBJECT = "家电测试用例设计与自检"
CASE_STEP_DESCRIPTION = (
    "按输入需求交付完整用例文档，必须包含：需求原子表、方法分配表、需求冲突登记表、"
    "13 字段测试用例、至少 3 条 E2E、覆盖与门禁自检、待确认问题。"
    "文档全文必须写在 handover 里，不能只交摘要或文件名。"
)
# 单个模块的首次 + 两次定点重写；截断不消耗重写次数。
CASE_MAX_ATTEMPTS = 3
# 输出 token 达到该值即视为顶到模型单次上限，模块直接拆分，不再送验收。
CASE_OUTPUT_TOKEN_LIMIT = 60_000
# 模块递归拆分的最大层数（0 为原始模块，最多再拆两层）。
CASE_MODULE_MAX_DEPTH = 2
# 一个模块文档至少应包含的后两节；缺节通常意味着输出被截断。
CASE_REQUIRED_SECTIONS = ("## 六、覆盖与门禁自检", "## 七、待确认问题")
# 交付正文短于该长度视为空交付（例如只有 <submission></submission> 标签）。
CASE_MIN_DOCUMENT_CHARS = 200


@dataclass(frozen=True)
class ModuleOutcome:
    """
    一个模块的验收结果。

    Attributes:
        key: 模块缩写。
        name: 模块名。
        start_line: 原始需求中的起始行号。
        end_line: 原始需求中的结束行号。
        passed: 该模块是否通过验收；截断模块恒为 False。
        truncated: 是否因输出超过上限被标记为截断。
        document_length: 该模块交付文档的字符数。
        message: 该模块最后一条验收意见或截断说明。
    """

    key: str
    name: str
    start_line: int
    end_line: int
    passed: bool
    truncated: bool
    document_length: int
    message: str = ""


@dataclass(frozen=True)
class CaseAuthoringResult:
    """
    一次用例编写运行的结果。

    Attributes:
        phase: 运行阶段；completed 表示全部模块通过。
        document: 交付文档；模块化运行时为按模块拼接的完整 Markdown。
        verdicts: 历次判决，元素为 (passed, message, verifier)，按时间顺序。
        truncated: 是否有模块因输出上限被截断且未能拆到可用粒度。
        max_output_tokens: 各次编写调用里最大的输出 token 数。
        modules: 每个模块的验收结果。
    """

    phase: str
    document: str
    verdicts: tuple[tuple[bool, str, str], ...]
    truncated: bool = False
    max_output_tokens: int = 0
    modules: tuple[ModuleOutcome, ...] = ()

    @property
    def passed(self) -> bool:
        """全部模块通过且没有截断时才算通过。"""
        if self.truncated:
            return False
        if self.modules:
            return all(module.passed for module in self.modules)
        return bool(self.verdicts) and self.verdicts[-1][0]


class _DraftRecordingStep(SOPStep):
    """
    记录每次尝试交付的用例文档，并在输出顶到上限时跳过验收。

    SOP 驳回时会清空 `state.submission`，这里在事件流上留一份副本，让失败的运行
    也能回看最后交上来的草稿；同时统计单次模型调用的最大输出 token，达到上限后
    把 verifier 置空，避免再花一次验收调用去判一份必然不完整的文档。

    Attributes:
        drafts: 按尝试顺序记录的交付文档，相邻重复只留一份。
        max_output_tokens: 本轮出现的最大模型输出 token。
        truncated: 是否出现输出上限或空交付。
        incomplete: 交付是否缺少第六/七节（可能被截断，也可能是质量问题）。
    """

    def __init__(self, *args, **kwargs) -> None:
        """按标准 SOP 步骤初始化，并准备草稿与截断标记。"""
        super().__init__(*args, **kwargs)
        self.drafts: list[str] = []
        self.max_output_tokens = 0
        self.truncated = False
        self.incomplete = False

    async def reply_stream(  # pylint: disable=invalid-overridden-method
        self,
        inputs: object,
        state: SOPStepRunState,
    ) -> AsyncGenerator[object, None]:
        """先记录交付再交给验收；输出顶到上限时跳过验收。"""
        async for event in super().reply_stream(inputs, state):
            if type(event).__name__ == "ModelCallEndEvent":
                output_tokens = int(getattr(event, "output_tokens", 0) or 0)
                self.max_output_tokens = max(self.max_output_tokens, output_tokens)
                if output_tokens >= CASE_OUTPUT_TOKEN_LIMIT:
                    self.truncated = True
                    # 基类在编写结束后才调用 verifier；置空即可跳过必然失败的判卷
                    self.verifier = None
            self._remember(state)
            yield event
        self._remember(state)
        self._check_document()

    def _remember(self, state: SOPStepRunState) -> None:
        """把当前交付正文收进 drafts；没有交付或与上一次相同时跳过。"""
        if not state.submission:
            return
        text = state.submission[0].text
        if not self.drafts or self.drafts[-1] != text:
            self.drafts.append(text)

    def _check_document(self) -> None:
        """空交付按截断处理；缺第六/七节记一条不完整标记。"""
        text = self.drafts[-1] if self.drafts else ""
        if len(text.strip()) < CASE_MIN_DOCUMENT_CHARS:
            self.truncated = True
            return
        missing = [section for section in CASE_REQUIRED_SECTIONS if section not in text]
        self.incomplete = bool(missing)


class CaseAuthoringWorkflow:
    """
    单个模块的用例编写 SOP：编写角色交文档，验收角色判卷，驳回后重写。

    Attributes:
        writer: 用例编写角色的 Agent。
        verifier: 用例验收角色的 Agent。
        max_attempts: 同一份文档最多尝试几次（含首次），默认三次。
    """

    def __init__(
        self,
        writer: Agent,
        verifier: Agent,
        max_attempts: int = CASE_MAX_ATTEMPTS,
    ) -> None:
        self.writer = writer
        self.verifier = verifier
        self.max_attempts = max(1, int(max_attempts))

    async def run(self, run_input: str) -> CaseAuthoringResult:
        """跑一次用例编写 SOP；截断时立即返回，不进入重写。

        Args:
            run_input: 需求正文与编写参数，由 `build_run_input` 生成。

        Returns:
            本次运行的阶段、交付文档与历次判决。

        Raises:
            asyncio.CancelledError: 任务被取消时由事件流抛回，本层不吞。
        """
        attempts: list[CaseAuthoringResult] = []
        current_input = run_input
        for attempt in range(1, self.max_attempts + 1):
            result = await self._run_once(current_input)
            attempts.append(result)
            if result.truncated or result.passed:
                break
            if attempt < self.max_attempts and result.verdicts:
                current_input = (
                    run_input
                    + "\n\n## 上一轮交付文档（只修下面意见点名的问题；未点名的段落、表格行、ID 与数字逐字保留）\n"
                    + (result.document or "（上一轮没有交付正文）")
                    + "\n\n## 上一轮验收意见（逐条修复；不要重写无关内容）\n"
                    + result.verdicts[-1][1]
                )

        last = attempts[-1]
        verdicts = tuple(verdict for result in attempts for verdict in result.verdicts)
        phase = "completed" if last.passed else "failed"
        max_tokens = max((result.max_output_tokens for result in attempts), default=0)
        self._log(f"用例编写运行结束：{phase}，模块文档 {len(last.document)} 字符")
        return CaseAuthoringResult(
            phase=phase,
            document=last.document,
            verdicts=verdicts,
            truncated=last.truncated,
            max_output_tokens=max_tokens,
        )

    async def _run_once(self, run_input: str) -> CaseAuthoringResult:
        """跑一次单步 SOP（不自动重写）。"""
        step = _DraftRecordingStep(
            subject=CASE_STEP_SUBJECT,
            description=CASE_STEP_DESCRIPTION,
            executor=self.writer,
            verifier=self.verifier,
            max_attempts=1,
        )
        engine = SOPEngine(SOP(name="家电测试用例编写", steps=[step]))
        models = {
            self.writer.name: self.writer.model.model,
            self.verifier.name: self.verifier.model.model,
        }
        buf: dict = {}
        async for event in engine.reply_stream(UserMsg(name="user", content=run_input)):
            # 用例编写没有设备截图，事件条数少；逐条落库让报告页能实时看到过程。
            await show_event(event, buf, models, flush=True)

        record = engine.state.steps[0]
        document = step.drafts[-1] if step.drafts else ""
        verdicts = tuple(
            (verdict.passed, verdict.message, verdict.verifier) for verdict in record.verifications
        )
        phase = str(getattr(engine.phase, "value", engine.phase) or "")
        return CaseAuthoringResult(
            phase=phase,
            document=document,
            verdicts=verdicts,
            truncated=step.truncated,
            max_output_tokens=step.max_output_tokens,
        )

    def _log(self, action: str) -> None:
        """运行汇总写入与设备执行链路同一份事件日志。"""
        model = getattr(getattr(self.writer, "model", None), "model", "") or "-"
        write_line(str(model), action)


@dataclass(frozen=True)
class _Draft:
    """模块流水线内部使用：一个模块及其编写结果。"""

    module: ModuleRange
    result: CaseAuthoringResult


def build_run_input(
    requirement_text: str,
    project_code: str = "",
    version: str = "",
    existing_cases: str = "",
    *,
    module_name: str = "",
    module_key: str = "",
    atom_start: int = 0,
) -> str:
    """把需求正文与编写参数拼成交给编写角色的开场输入。

    Args:
        requirement_text: 需求正文；模块化模式下只传该模块的片段。
        project_code: 项目代号，用于用例编号；空时用 PROJ。
        version: 版本号，用于用例编号；空时用 V1。
        existing_cases: 已有用例索引；空时按全新模式。
        module_name: 模块名；为空表示整份文档模式。
        module_key: 模块缩写；非空时开启模块化交付。
        atom_start: 本模块原子编号起始号；0 表示不限制区段。

    Returns:
        带小标题的开场输入。

    Raises:
        ValueError: 需求正文为空白。
    """
    requirement = requirement_text.strip()
    if not requirement:
        raise ValueError("需求正文不能为空")
    scope = ""
    if module_key:
        start = max(int(atom_start or 1), 1)
        scope = (
            "## 本次模块\n"
            f"- 模块名：{module_name or module_key}\n"
            f"- 模块KEY：{module_key}\n"
            f"- 原子编号区段：REQ-{start:03d} ~ REQ-{start + 99:03d}（从起始号连续分配）\n\n"
        )
        heading = "## 本模块需求片段"
    else:
        heading = "## 需求正文"
    return (
        scope
        + f"{heading}\n"
        + f"{requirement}\n\n"
        + "## 项目代号\n"
        + f"{project_code.strip() or 'PROJ'}\n\n"
        + "## 版本号\n"
        + f"{version.strip() or 'V1'}\n\n"
        + "## 已有用例索引\n"
        + f"{existing_cases.strip() or '（无，按全新模式全量生成）'}\n"
    )


def _module_outcome(module: ModuleRange, result: CaseAuthoringResult) -> ModuleOutcome:
    """把一次模块运行收成可写入任务结果的摘要。"""
    if result.truncated:
        message = "输出超过单次上限，已拆到最小块仍截断（OUTPUT_TRUNCATED）"
    else:
        message = result.verdicts[-1][1] if result.verdicts else ""
    return ModuleOutcome(
        key=module.key,
        name=module.name,
        start_line=module.start_line,
        end_line=module.end_line,
        passed=bool(result.passed),
        truncated=result.truncated,
        document_length=len(result.document or ""),
        message=message[:2000],
    )


async def run_case_authoring_modules(
    requirement_text: str,
    project_code: str = "",
    version: str = "",
    existing_cases: str = "",
    *,
    cancel_event=None,
) -> CaseAuthoringResult:
    """
    模块化用例编写：规划 → 逐模块编写/验收 → 截断拆分 → 拼装。

    Args:
        requirement_text: 需求正文。
        project_code: 项目代号。
        version: 版本号。
        existing_cases: 已有用例索引。
        cancel_event: `threading.Event` 取消信号；每个模块开始前检查。

    Returns:
        合并后的文档、判决、模块清单与截断标记。

    Raises:
        asyncio.CancelledError: 取消信号置位时抛出，由任务层映射为 cancelled。
        ValueError: 需求正文为空白。
    """
    modules = await plan_case_modules(requirement_text, project_code, version)
    if not modules:
        raise ValueError("需求正文不能为空")

    drafts: list[_Draft] = []
    store = ModuleStore()
    atom_cursor = 1

    def check_cancel() -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise asyncio.CancelledError

    async def generate(module: ModuleRange, depth: int) -> None:
        """生成一个模块；截断且还能拆时递归拆成两半。"""
        nonlocal atom_cursor
        check_cancel()
        full = module.key == "ALL" and depth == 0 and len(modules) == 1
        start = 0 if full else atom_cursor
        if not full:
            atom_cursor += 100
        run_input = build_run_input(
            module.text if not full else requirement_text,
            project_code=project_code,
            version=version,
            existing_cases=existing_cases,
            module_name="" if full else module.name,
            module_key="" if full else module.key,
            atom_start=0 if full else start,
        )
        set_case_title(f"{module.name}（{module.key}）")
        if os.getenv("CASE_AUTHORING_ENGINE", "goal").lower() == "sop":
            workflow = CaseAuthoringWorkflow(
                build_case_writer().agent,
                build_case_verifier().agent,
            )
            result = await workflow.run(run_input)
        else:
            goal = await run_goal_module(run_input, module.key, store)
            result = CaseAuthoringResult(
                phase="completed" if goal.passed else "failed",
                document=goal.document,
                verdicts=goal.verdicts,
                truncated=goal.truncated,
                max_output_tokens=goal.max_output_tokens,
            )
        if result.truncated and depth < CASE_MODULE_MAX_DEPTH:
            parts = split_module(module)
            if parts:
                await generate(parts[0], depth + 1)
                await generate(parts[1], depth + 1)
                return
        drafts.append(_Draft(module=module, result=result))

    for module in modules:
        await generate(module, 0)

    outcomes = tuple(_module_outcome(draft.module, draft.result) for draft in drafts)
    single_full = len(modules) == 1 and modules[0].key == "ALL" and len(drafts) == 1
    verdicts = tuple(
        (
            passed,
            ("" if single_full else f"[模块 {draft.module.key}] ") + message,
            verifier,
        )
        for draft in drafts
        if not draft.result.truncated
        for passed, message, verifier in draft.result.verdicts
    )
    if any(draft.result.truncated for draft in drafts):
        verdicts = verdicts + (
            (
                False,
                "部分模块输出超过单次上限且已拆到最小块，见模块清单中的 truncated 标记",
                "case_verifier_role",
            ),
        )
    passed = bool(outcomes) and all(outcome.passed for outcome in outcomes)
    if single_full:
        document = drafts[0].result.document
    else:
        document = build_module_document(
            [(draft.module, draft.result) for draft in drafts],
            project_code,
            version,
        )
    max_tokens = max((draft.result.max_output_tokens for draft in drafts), default=0)
    return CaseAuthoringResult(
        phase="completed" if passed else "failed",
        document=document,
        verdicts=verdicts,
        truncated=any(draft.result.truncated for draft in drafts),
        max_output_tokens=max_tokens,
        modules=outcomes,
    )


def run_case_authoring(
    requirement_text: str,
    project_code: str = "",
    version: str = "",
    existing_cases: str = "",
) -> CaseAuthoringResult:
    """装配一次模块化用例编写并跑完（同步入口）。

    Args:
        requirement_text: 需求正文。
        project_code: 项目代号。
        version: 版本号。
        existing_cases: 已有用例索引。

    Returns:
        合并后的运行结果。

    Raises:
        ValueError: 需求正文为空白。
    """
    return asyncio.run(
        run_case_authoring_modules(
            requirement_text,
            project_code=project_code,
            version=version,
            existing_cases=existing_cases,
        )
    )
