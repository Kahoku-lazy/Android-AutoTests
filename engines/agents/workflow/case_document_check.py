"""
python - 调试路径: engines.agents.workflow.case_document_check

本模块的业务功能如下：
1. ParsedCaseDocument: 从 Markdown 用例文档解析原子表、用例表与 E2E 数。
2. check_case_document: 用代码核对 ID、13 字段、方法数门槛、优先级比例、覆盖率与模糊词。
3. fix_case_statistics: 用代码重算并回写第六节统计，避免模型自检数字与表格不一致。
"""

from __future__ import annotations

import re

from collections import Counter
from dataclasses import dataclass, field

CASE_FIELDS = (
    "用例编号",
    "测试标题",
    "追溯ID",
    "方法",
    "复杂度",
    "优先级",
    "前置条件",
    "测试步骤",
    "预期结果",
    "量化指标",
    "校验要点",
    "状态",
    "执行记录",
)
STATUS_VALUES = {"PASS", "FAIL", "SKIP", "BLOCKED", "UNCERTAIN", "NOT_RUN"}
METHOD_FLOOR = {"L1": 2, "L2": 3, "L3": 4, "L4": 4}
FUZZY_WORDS = (
    "正常",
    "稳定",
    "良好",
    "符合预期",
    "无明显异常",
    "无异常",
    "尽快",
    "适当",
    "合理",
    "友好",
)
PLACEHOLDERS = {"", "-", "—", "待补充", "TBD", "N/A"}


@dataclass
class CaseRow:
    """一条用例表行。"""

    case_id: str
    fields: dict[str, str]
    traces: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    complexity: str = ""
    priority: str = ""
    status: str = ""
    module: str = ""


@dataclass
class ParsedCaseDocument:
    """解析后的用例文档。"""

    atoms: dict[str, str]
    cases: list[CaseRow]
    e2e_count: int
    sections: set[str]


def _clean_header(value: str) -> str:
    """表头去掉粗体、反引号、空格与冒号。"""
    return re.sub(r"[\s`*:：]", "", value or "")


def _split_cells(line: str) -> list[str]:
    """按 Markdown 管道拆分一行；首尾管道不算单元格。"""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    """表头下的 `|---|:--:|` 分隔行。"""
    cells = _split_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell or "-") for cell in cells)


def _tables(lines: list[str]) -> list[tuple[int, list[str]]]:
    """收集 Markdown 管道表及表头所在行号。"""
    tables: list[tuple[int, list[str]]] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip().startswith("|"):
            index += 1
            continue
        start = index
        block: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            block.append(lines[index].strip())
            index += 1
        if len(block) >= 2:
            tables.append((start, block))
    return tables


def _module_at(lines: list[str], start: int) -> str:
    """取表格之前最近的模块标题；没有模块标题时回退到 4.x 子标题。"""
    module = ""
    subsection = ""
    for line in lines[:start]:
        stripped = line.strip()
        module_match = re.match(r"^##\s*模块[：:]\s*([^（(]+)", stripped)
        if module_match:
            module = module_match.group(1).strip()
            subsection = ""
            continue
        subsection_match = re.match(r"^###\s*4\.\d+\s+(.+)$", stripped)
        if subsection_match:
            subsection = subsection_match.group(1).strip()
            continue
        if stripped.startswith("## "):
            subsection = ""
    return module or subsection


def _column(header: list[str], *aliases: str) -> int | None:
    """在表头里找第一个匹配的列号。"""
    normalized = [_clean_header(cell) for cell in header]
    for alias in aliases:
        target = _clean_header(alias)
        for index, value in enumerate(normalized):
            if value == target or value.startswith(target):
                return index
    return None


def _cell(row: list[str], index: int | None) -> str:
    """取单元格；越界返回空串。"""
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def _split_ids(value: str) -> list[str]:
    """拆分追溯 ID。"""
    return [part for part in re.split(r"[,，、;；\s]+", value or "") if part]


def _split_methods(value: str) -> list[str]:
    """拆分方法列，避免把 `边界值+等价类` 当成一种。"""
    return [part for part in re.split(r"[+＋、,，;；/]+", value or "") if part.strip()]


def parse_case_document(markdown: str) -> ParsedCaseDocument:
    """解析 Markdown 文档里的原子表、用例表、E2E 与七节标题。"""
    lines = markdown.splitlines()
    sections = {
        match.group(1)
        for line in lines
        if (match := re.match(r"^##\s*([一二三四五六七])、", line.strip()))
    }
    atoms: dict[str, str] = {}
    cases: list[CaseRow] = []
    e2e_count = 0

    for table_start, table in _tables(lines):
        module = _module_at(lines, table_start)
        header = _split_cells(table[0])
        data = [row for row in table[1:] if not _is_separator(row)]
        atom_id_col = _column(header, "原子ID", "原子编号")
        case_id_col = _column(header, "用例编号")
        e2e_id_col = _column(header, "E2E编号", "E2E")

        if atom_id_col is not None and _column(header, "需求原子") is not None:
            note_col = _column(header, "备注")
            for row in data:
                cells = _split_cells(row)
                atom_id = _cell(cells, atom_id_col)
                if atom_id.startswith("REQ-"):
                    atoms[atom_id] = _cell(cells, note_col)
            continue

        if case_id_col is not None and _column(header, "追溯ID", "追溯需求ID") is not None:
            trace_col = _column(header, "追溯ID", "追溯需求ID")
            for row in data:
                cells = _split_cells(row)
                case_id = _cell(cells, case_id_col)
                if not case_id.startswith("TC-"):
                    continue
                fields = {name: _cell(cells, _column(header, name)) for name in CASE_FIELDS}
                cases.append(
                    CaseRow(
                        case_id=case_id,
                        fields=fields,
                        traces=_split_ids(_cell(cells, trace_col)),
                        methods=_split_methods(_cell(cells, _column(header, "方法", "设计方法"))),
                        complexity=_cell(cells, _column(header, "复杂度")),
                        priority=_cell(cells, _column(header, "优先级")),
                        status=_cell(cells, _column(header, "状态", "执行状态")),
                        module=module,
                    )
                )
            continue

        if e2e_id_col is not None:
            e2e_count += sum(
                1 for row in data if _cell(_split_cells(row), e2e_id_col).startswith("E2E-")
            )

    return ParsedCaseDocument(atoms=atoms, cases=cases, e2e_count=e2e_count, sections=sections)


def _split_step_cell(value: str) -> list[str]:
    """按 ``<br>`` 拆单元格并去掉 ``1)`` / ``1.`` 序号前缀。"""
    parts = re.split(r"<br\s*/?>", value or "", flags=re.IGNORECASE)
    cleaned: list[str] = []
    for part in parts:
        text = re.sub(r"^\s*(?:\d+[.)、]|[①②③④⑤⑥⑦⑧⑨⑩])\s*", "", part.strip())
        if text:
            cleaned.append(text)
    return cleaned


def case_step_pairs(case: CaseRow) -> list[tuple[str, str]]:
    """把一条用例的测试步骤与预期结果按顺序配成步骤对。

    两侧条目数一致时逐条配对；任一侧为空时返回空列表；数量不一致时退化为
    一条完整步骤，避免猜测缺失的对应关系。

    Args:
        case: 已解析的用例行。

    Returns:
        ``[(action, assertion), ...]``，按文档出现顺序。
    """
    actions = _split_step_cell(case.fields.get("测试步骤", ""))
    assertions = _split_step_cell(case.fields.get("预期结果", ""))
    if not actions or not assertions:
        return []
    if len(actions) == len(assertions):
        return list(zip(actions, assertions, strict=True))
    return [("；".join(actions), "；".join(assertions))]


def _coverage(parsed: ParsedCaseDocument) -> tuple[int, int, int]:
    """返回 (已覆盖原子数, 已判定原子数, 总原子数)。"""
    covered = {atom for case in parsed.cases for atom in case.traces if atom in parsed.atoms}
    judged = {
        atom
        for case in parsed.cases
        if case.status not in {"UNCERTAIN", "SKIP"}
        for atom in case.traces
        if atom in parsed.atoms
    }
    return len(covered), len(judged), len(parsed.atoms)


def _method_counts(parsed: ParsedCaseDocument) -> Counter:
    """按用例表逐条统计方法使用次数。"""
    counter: Counter = Counter()
    for case in parsed.cases:
        for method in case.methods:
            counter[method.strip()] += 1
    return counter


def _priority_counts(parsed: ParsedCaseDocument) -> Counter:
    """P0/P1/P2 用例数。"""
    return Counter(case.priority for case in parsed.cases)


def check_case_document(markdown: str) -> list[str]:
    """用代码核对文档结构、ID、字段、方法数、优先级与覆盖率。"""
    parsed = parse_case_document(markdown)
    issues: list[str] = []

    missing = [section for section in "一二三四五六七" if section not in parsed.sections]
    if missing:
        issues.append(f"缺少章节：{'、'.join('第' + item + '节' for item in missing)}")
    if not parsed.atoms:
        issues.append("未解析到需求原子表，或表头缺少「原子ID / 需求原子」")
    if not parsed.cases:
        issues.append("未解析到用例表，或表头缺少「用例编号 / 追溯ID」")

    atom_ids = list(parsed.atoms)
    if len(atom_ids) != len(set(atom_ids)):
        issues.append("需求原子表存在重复原子ID")
    case_ids = [case.case_id for case in parsed.cases]
    if len(case_ids) != len(set(case_ids)):
        issues.append("用例表存在重复用例编号")

    covered, _judged, total = _coverage(parsed)
    missing_atoms = [
        atom
        for atom in parsed.atoms
        if atom not in {value for case in parsed.cases for value in case.traces}
        and not re.search(r"UNTESTABLE|SKIP|不可测", parsed.atoms[atom], re.IGNORECASE)
    ]
    if missing_atoms:
        issues.append(f"未被任何用例覆盖的原子：{', '.join(missing_atoms[:12])}")

    for case in parsed.cases:
        for atom in case.traces:
            if atom not in parsed.atoms:
                issues.append(f"{case.case_id} 追溯了原子表之外的 ID：{atom}")
        for name in CASE_FIELDS:
            value = case.fields.get(name, "").strip()
            if value in PLACEHOLDERS:
                issues.append(f"{case.case_id} 的「{name}」为空或占位符")
        if case.status and case.status not in STATUS_VALUES:
            issues.append(f"{case.case_id} 的执行状态非法：{case.status}")
        if case.status == "UNTESTABLE":
            issues.append(f"{case.case_id} 把 UNTESTABLE 当成执行状态")
        floor = METHOD_FLOOR.get(case.complexity)
        if floor is None:
            issues.append(f"{case.case_id} 的复杂度非法：{case.complexity or '空'}")
        elif len(case.methods) < floor:
            issues.append(
                f"{case.case_id} 复杂度 {case.complexity} 只有 {len(case.methods)} 种方法，低于 {floor}"
            )
        for word in FUZZY_WORDS:
            if word in case.fields.get("预期结果", ""):
                issues.append(f"{case.case_id} 的预期结果含模糊词「{word}」")
                break

    priorities = _priority_counts(parsed)
    unknown_priority = [key for key in priorities if key not in {"P0", "P1", "P2"}]
    if unknown_priority:
        issues.append(f"用例优先级非法：{', '.join(unknown_priority)}")
    total_cases = len(parsed.cases)
    if total_cases and priorities.get("P0", 0) / total_cases > 0.3:
        issues.append(f"P0 用例 {priorities.get('P0', 0)}/{total_cases} 超过 30%")

    if parsed.e2e_count < 3:
        issues.append(f"E2E 用例只有 {parsed.e2e_count} 条，少于 3 条")
    if total and covered / total < 0.7:
        issues.append(f"原子覆盖 {covered}/{total} 低于 70%")

    return issues


def _statistics_block(parsed: ParsedCaseDocument) -> str:
    """按解析结果生成第六节统计表。"""
    atom_total = len(parsed.atoms)
    case_total = len(parsed.cases)
    priorities = _priority_counts(parsed)
    covered, judged, _total = _coverage(parsed)
    methods = _method_counts(parsed)

    def percent(part: int) -> str:
        return f"{part / case_total * 100:.1f}%" if case_total else "0.0%"

    p0 = priorities.get("P0", 0)
    p1 = priorities.get("P1", 0)
    p2 = priorities.get("P2", 0)
    method_text = "；".join(f"{name} {count}" for name, count in sorted(methods.items())) or "无"
    return "\n".join(
        [
            "## 六、覆盖与门禁自检",
            "",
            "| 指标 | 数值 | 结论 |",
            "|------|:--:|------|",
            f"| 需求原子数 | {atom_total} | 代码统计 |",
            f"| 用例数 | {case_total} | 代码统计 |",
            (
                f"| P0 / P1 / P2 用例数及占比 | P0={p0}（{percent(p0)}）/ "
                f"P1={p1}（{percent(p1)}）/ P2={p2}（{percent(p2)}） | "
                f"P0 占比 {percent(p0)} ≤30% |"
            ),
            f"| 已判定覆盖率（不含 UNCERTAIN / SKIP） | {judged}/{atom_total} | 代码统计 |",
            f"| 已登记覆盖率（含 UNCERTAIN / SKIP） | {covered}/{atom_total} | 代码统计 |",
            f"| 方法使用统计 | {method_text} | 按用例表逐条计数 |",
            f"| E2E 条数 | {parsed.e2e_count} | {'≥3' if parsed.e2e_count >= 3 else '少于 3'} |",
        ]
    )


def fix_case_statistics(markdown: str) -> str:
    """把第六节替换成代码统计表；找不到第六节时原样返回。"""
    lines = markdown.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if re.match(r"^##\s*六、", line.strip())),
        None,
    )
    if start is None:
        return markdown
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if re.match(r"^##\s*七、", lines[index].strip())
        ),
        len(lines),
    )
    block = _statistics_block(parse_case_document(markdown)).splitlines()
    return "\n".join(lines[:start] + block + [""] + lines[end:])


def check_and_fix_document(markdown: str) -> tuple[str, list[str]]:
    """先校验，再用代码统计回写第六节，返回修正后的文档与问题列表。"""
    issues = check_case_document(markdown)
    return fix_case_statistics(markdown), issues
