"""
python -m 调试路径: engines.agents.workflow.case_module_plan

本模块的业务功能如下：
1. ModulePlan / ModuleSpec: 模块规划角色输出的结构化契约。
2. ModuleRange: 一个模块的行号区间与切出的需求正文。
3. plan_case_modules: 让规划角色切分需求；输出非法时按标题或固定行数回退。
4. split_module: 输出截断时把一个模块区间一分为二。
5. build_module_document: 把逐模块结果拼成一份带模块标题的 Markdown。
"""

from __future__ import annotations

import re

from dataclasses import dataclass

from agentscope.message import Msg, UserMsg
from pydantic import BaseModel, Field

from engines.agents.role.case_roles import build_case_planner
from engines.agents.workflow.ui_auto_workflow import show_event

# 规划输出的硬边界：低于该行数不拆；高于该值的单块按回退策略再切。
MIN_SPLIT_LINES = 80
MAX_MODULES = 12
MIN_MODULE_LINES = 20
# 回退切块时每块的目标原始行数（没有章节标题的 PDF 转换稿尤其需要）。
FALLBACK_CHUNK_LINES = 120
# 规划区间至少要覆盖的非空行比例；低于它视为漏段，整份回退。
MIN_COVERAGE = 0.6


class ModuleSpec(BaseModel):
    """规划角色给出的一个模块区间。"""

    key: str = Field(description="3-4 个大写字母的模块缩写，全文唯一")
    name: str = Field(description="2-12 个汉字的模块名")
    start_line: int = Field(description="模块起始行号，1 起，闭区间")
    end_line: int = Field(description="模块结束行号，1 起，闭区间")


class ModulePlan(BaseModel):
    """规划角色的完整输出。"""

    modules: list[ModuleSpec] = Field(default_factory=list)


@dataclass(frozen=True)
class ModuleRange:
    """
    一个模块的行号区间与需求正文。

    Attributes:
        key: 3-4 个大写字母缩写，用于原子/用例/E2E 编号。
        name: 模块中文名。
        start_line: 起始行号（1 起，闭区间）。
        end_line: 结束行号（1 起，闭区间）。
        text: 该区间切出的需求正文。
    """

    key: str
    name: str
    start_line: int
    end_line: int
    text: str


def _numbered(text: str) -> str:
    """把需求正文写成 `行号| 原文`，供规划角色引用真实行号。"""
    return "\n".join(f"{index}| {line}" for index, line in enumerate(text.splitlines(), start=1))


def _slice(lines: list[str], start_line: int, end_line: int) -> str:
    """取 1 起闭区间的正文；越界时自动夹取。"""
    first = max(int(start_line), 1)
    last = min(int(end_line), len(lines))
    if last < first:
        return ""
    return "\n".join(lines[first - 1 : last])


def _sanitize_key(raw: str, index: int, used: set[str]) -> str:
    """把模型给的 key 收成 3-4 位大写字母；冲突时补序号。"""
    letters = re.sub(r"[^A-Z]", "", str(raw or "").upper())[:4]
    key = letters if len(letters) >= 3 else f"M{index:02d}"
    if key not in used:
        used.add(key)
        return key
    for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        candidate = f"{key[:3]}{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
    fallback = f"M{index:02d}"
    used.add(fallback)
    return fallback


def _heading_rows(lines: list[str]) -> list[int]:
    """找出章节标题所在行号（1 起）。"""
    rows: list[int] = []
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            rows.append(index)
            continue
        if len(stripped) <= 80 and re.match(r"^\d+(\.\d+){0,3}[、.\s]", stripped):
            rows.append(index)
    return rows


def fallback_modules(text: str) -> tuple[ModuleRange, ...]:
    """
    规划失败或输出不可用时的确定性回退切块。

    有足够章节标题时按标题分组，每块约 5 个章节；没有标题的 PDF 转换稿按
    120 行一块。行数很少时只返回一个模块。

    Args:
        text: 需求正文。

    Returns:
        至少一个模块区间。
    """
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return ()
    if len(non_empty) <= MIN_SPLIT_LINES:
        return (ModuleRange("ALL", "全部需求", 1, max(len(lines), 1), text),)

    headings = _heading_rows(lines)
    chunks: list[tuple[int, int]] = []
    if len(headings) >= 6:
        per_chunk = max(1, (len(headings) + 4) // 5)
        for offset in range(0, len(headings), per_chunk):
            start = headings[offset]
            end = (
                headings[offset + per_chunk] - 1
                if offset + per_chunk < len(headings)
                else len(lines)
            )
            if end >= start:
                chunks.append((start, end))
    else:
        start = 1
        while start <= len(lines):
            end = min(start + FALLBACK_CHUNK_LINES - 1, len(lines))
            chunks.append((start, end))
            start = end + 1

    used: set[str] = set()
    modules: list[ModuleRange] = []
    for index, (start, end) in enumerate(chunks, start=1):
        body = _slice(lines, start, end)
        if not body.strip():
            continue
        heading = next((line.strip("# ").strip() for line in body.splitlines() if line.strip()), "")
        modules.append(
            ModuleRange(
                key=_sanitize_key("", index, used),
                name=(heading or f"需求片段 {index}")[:40],
                start_line=start,
                end_line=end,
                text=body,
            )
        )
    return tuple(modules) or (ModuleRange("ALL", "全部需求", 1, len(lines), text),)


def _coverage(lines: list[str], modules: tuple[ModuleRange, ...]) -> float:
    """规划区间覆盖到的非空行比例。"""
    non_empty = {index for index, line in enumerate(lines, start=1) if line.strip()}
    if not non_empty:
        return 1.0
    covered = set()
    for module in modules:
        covered.update(range(module.start_line, module.end_line + 1))
    return len(non_empty & covered) / len(non_empty)


def normalize_modules(text: str, specs: list[ModuleSpec]) -> tuple[ModuleRange, ...]:
    """
    校验并修正规划角色的区间：排序、夹取、去重叠、补 key、检查覆盖率。

    Args:
        text: 需求正文。
        specs: 规划角色给出的模块列表。

    Returns:
        可用的模块区间；不合规时退回 `fallback_modules`。
    """
    lines = text.splitlines()
    if not lines:
        return ()
    ordered = sorted(
        (spec for spec in specs if spec.start_line and spec.end_line),
        key=lambda spec: (int(spec.start_line), int(spec.end_line)),
    )
    used: set[str] = set()
    modules: list[ModuleRange] = []
    cursor = 1
    for index, spec in enumerate(ordered, start=1):
        start = max(int(spec.start_line), cursor)
        end = min(int(spec.end_line), len(lines))
        if end < start:
            continue
        body = _slice(lines, start, end)
        if not body.strip():
            cursor = end + 1
            continue
        modules.append(
            ModuleRange(
                key=_sanitize_key(spec.key, index, used),
                name=(spec.name or f"模块 {index}").strip()[:40],
                start_line=start,
                end_line=end,
                text=body,
            )
        )
        cursor = end + 1

    if not modules:
        return fallback_modules(text)
    if len(modules) > MAX_MODULES:
        return fallback_modules(text)
    if _coverage(lines, tuple(modules)) < MIN_COVERAGE:
        return fallback_modules(text)
    if len(modules) == 1 and sum(1 for line in lines if line.strip()) > MIN_SPLIT_LINES * 2:
        return fallback_modules(text)
    return tuple(modules)


async def _ask_planner(
    requirement_text: str,
    project_code: str,
    version: str,
    planner_factory,
) -> list[ModuleSpec]:
    """调一次规划角色，返回原始模块列表；模型或解析失败时抛异常。"""
    planner = planner_factory()
    role = getattr(planner, "role", None)
    agent = getattr(planner, "agent", None)
    if agent is None:
        raise ValueError("规划角色缺少 agent")
    models = {
        str(getattr(role, "name", "") or "case_planner_role"): str(
            getattr(getattr(agent, "model", None), "model", "") or ""
        )
    }
    prompt = (
        "## 项目代号\n"
        f"{project_code or 'PROJ'}\n\n"
        "## 版本号\n"
        f"{version or 'V1'}\n\n"
        "## 带行号的需求正文\n"
        f"{_numbered(requirement_text)}\n"
    )
    buf: dict = {}
    final: Msg | None = None
    async for event in agent.reply_stream(
        inputs=UserMsg(name="user", content=prompt),
        structured_schema=ModulePlan,
        yield_final_msg=True,
    ):
        if isinstance(event, Msg):
            final = event
            continue
        await show_event(event, buf, models, flush=True)
    if final is None or not final.structured_output:
        raise ValueError("规划角色没有给出结构化输出")
    plan = ModulePlan.model_validate(final.structured_output)
    return list(plan.modules)


async def plan_case_modules(
    requirement_text: str,
    project_code: str = "",
    version: str = "",
    *,
    planner_factory=build_case_planner,
) -> tuple[ModuleRange, ...]:
    """
    把需求正文切成可独立编写/验收的模块。

    规划角色失败、输出为空或区间不合规时，退回按标题/固定行数的确定性切块。
    需求非空行不足 `MIN_SPLIT_LINES` 时直接作为一个模块，不浪费规划调用。

    Args:
        requirement_text: 需求正文。
        project_code: 项目代号，仅作规划上下文。
        version: 版本号，仅作规划上下文。
        planner_factory: 规划角色工厂，测试可替换。

    Returns:
        按原文顺序排列的模块区间；需求为空时返回空元组。

    Raises:
        ValueError: 需求正文为空白。
    """
    text = (requirement_text or "").strip()
    if not text:
        raise ValueError("需求正文不能为空")
    lines = text.splitlines()
    non_empty = sum(1 for line in lines if line.strip())
    if non_empty <= MIN_SPLIT_LINES:
        return (ModuleRange("ALL", "全部需求", 1, len(lines), text),)
    try:
        specs = await _ask_planner(text, project_code, version, planner_factory)
    except Exception:
        return fallback_modules(text)
    modules = normalize_modules(text, specs)
    return modules or fallback_modules(text)


def split_module(module: ModuleRange) -> tuple[ModuleRange, ModuleRange] | None:
    """
    把一个模块区间一分为二，供输出截断时继续拆分。

    分割点取区间中点之后最近的一个空行；找不到空行就用中点。两半都必须
    至少有 5 行、且正文非空，否则返回 None（不再拆）。

    Args:
        module: 待拆分的模块。

    Returns:
        两个新模块；无法再拆时返回 None。
    """
    lines = module.text.splitlines()
    if len(lines) < 10:
        return None
    middle = len(lines) // 2
    split_at = middle
    for offset in range(middle, min(len(lines) - 5, middle + 20)):
        if not lines[offset].strip():
            split_at = offset
            break
    if split_at < 5 or len(lines) - split_at < 5:
        return None

    first_text = "\n".join(lines[:split_at]).strip("\n")
    second_text = "\n".join(lines[split_at:]).strip("\n")
    if not first_text.strip() or not second_text.strip():
        return None
    base = module.key[:3]
    return (
        ModuleRange(
            key=f"{base}A",
            name=f"{module.name}（上）",
            start_line=module.start_line,
            end_line=module.start_line + split_at - 1,
            text=first_text,
        ),
        ModuleRange(
            key=f"{base}B",
            name=f"{module.name}（下）",
            start_line=module.start_line + split_at,
            end_line=module.end_line,
            text=second_text,
        ),
    )


def build_module_document(
    modules: list[tuple[ModuleRange, object]],
    project_code: str = "",
    version: str = "",
) -> str:
    """
    把逐模块的编写结果拼成一份 Markdown。

    Args:
        modules: (模块区间, 编写结果) 列表；结果需有 `document` 与 `passed` 属性。
        project_code: 项目代号，写进标题。
        version: 版本号，写进标题。

    Returns:
        拼接后的完整文档；没有模块时返回空串。
    """
    if not modules:
        return ""
    header = [
        f"# 家电测试用例（{project_code or 'PROJ'} / {version or 'V1'}）",
        "",
        f"> 需求按模块拆分为 {len(modules)} 份，每份独立编写与验收；以下按模块顺序拼接。",
    ]
    parts = ["\n".join(header)]
    for module, result in modules:
        status = "PASS" if bool(getattr(result, "passed", False)) else "FAIL"
        body = str(getattr(result, "document", "") or "").strip()
        parts.append(f"\n---\n\n## 模块：{module.name}（{module.key}）· 验收 {status}\n\n{body}")
    return "\n".join(parts)
