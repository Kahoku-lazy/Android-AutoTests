"""规划模型能力评测：批量跑用例 → 机械校验 → 控制台总表 + 报告。

用法（不走前端，不需要设备）：

    python manage.py planner_eval --cases tests/ai_planner/cases/planner.yaml \
        --repeat 2 --tag deepseek-flash

设计要点（见 openspec/changes/archive/2026-10-08-add-planner-eval/design.md）：

- **生产同源装配**：复用 `model_debug.build_device_models_for_agent`（与 `model_test`、模型调试台
  同一份装配），只取 planner 角色——否则测的不是生产实际那份提示词与工具子集。
- **判据分两级**：硬性项（契约 / 关键词覆盖 / 步骤数区间 / 页面流工具 / 日志标记区分度）判失败；
  疑似项（多副作用动作、断言空话、结构不稳定）只提示不判失败——提示词本身规定的
  "先找到元素，再点击"句式合法，机械当失败会制造假红。
- **不碰生产**：不写库、不建任务、不占设备池；命令始终以 0 退出（评测不是门禁）。
"""

from __future__ import annotations

import asyncio
import json
import re
import time

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.api import get_platform_agent
from apps.ai_assistant.engine_adapter import build_tool_specs
from apps.ai_assistant.model_debug import build_device_models_for_agent
from apps.ai_assistant.skills_catalog import list_enabled_skill_dirs
from engines.ai.agents import build_device_models
from engines.ai.workflow.workflow import Plan, _coerce, _parse_json

DEFAULT_REPORT_DIR = "tests/reports/planner_eval"

# 副作用动作动词：用于"一步多动作"疑似判定（读取类不计）
SIDE_EFFECT_VERBS = (
    "点击",
    "输入",
    "滑动",
    "拖动",
    "长按",
    "启动",
    "打开",
    "返回",
    "关闭",
    "开启",
    "切换",
    "选择",
    "上传",
    "下载",
)
# 并列连接词：与"多个副作用动作"同时出现才判疑似（提示词允许"先找到…再点击"）
CONJUNCTIONS = ("然后", "并且", "并", "同时", "接着", "之后")
# 断言空话：这些写法不构成"可观察结果"（不含裸"成功"，避免误伤"启动成功并停留在…"这类有效断言）
EMPTY_ASSERT_PATTERNS = ("操作成功", "执行成功", "成功完成", "没有问题", "一切正常", "任务完成")


# ── 用例模型与加载 ──


@dataclass
class EvalCase:
    """一条评测用例：需求 + 机械可判的期望。"""

    id: str
    title: str
    goal: str
    input_kind: str = "text"  # text（直接喂 goal）| json（四键 JSON，可带附件与设备）
    attach: str = ""
    device: str = ""
    must_contain: list[str] = field(default_factory=list)
    steps_min: int = 1
    steps_max: int = 99
    require_flow_tool: bool = True
    expect_mixed_log_check: bool = False
    repeat: int | None = None


def build_case(raw: dict) -> EvalCase:
    """YAML 条目 → EvalCase（字段非法时给出指向该用例 id 的可读错误）。"""
    case_id = str(raw.get("id") or "").strip()
    if not case_id:
        raise ValueError("用例缺少 id")
    expect = raw.get("expect") or {}
    input_kind = str(raw.get("input") or "text").strip().lower()
    if input_kind not in ("text", "json"):
        raise ValueError(f"用例 {case_id} 的 input 只能是 text 或 json")
    case = EvalCase(
        id=case_id,
        title=str(raw.get("title") or case_id).strip(),
        goal=str(raw.get("goal") or "").strip(),
        input_kind=input_kind,
        attach=str(raw.get("attach") or ""),
        device=str(raw.get("device") or ""),
        must_contain=[str(x) for x in (expect.get("must_contain") or []) if str(x).strip()],
        steps_min=int(expect.get("steps_min", 1)),
        steps_max=int(expect.get("steps_max", 99)),
        require_flow_tool=bool(expect.get("require_flow_tool", True)),
        expect_mixed_log_check=bool(expect.get("expect_mixed_log_check", False)),
        repeat=raw.get("repeat"),
    )
    if not case.goal:
        raise ValueError(f"用例 {case_id} 的 goal 为空")
    if case.steps_min > case.steps_max:
        raise ValueError(f"用例 {case_id} 的 steps_min 大于 steps_max")
    return case


def load_cases(path: str | Path) -> list[EvalCase]:
    """加载用例集：支持单个 YAML 文件（列表或 cases:）或目录（读该目录下 *.yaml / *.yml）。"""
    target = Path(path)
    if not target.exists():
        raise ValueError(f"用例路径不存在：{target}")
    files = sorted([*target.glob("*.yaml"), *target.glob("*.yml")]) if target.is_dir() else [target]
    if not files:
        raise ValueError(f"用例目录下没有 yaml：{target}")

    cases: list[EvalCase] = []
    for file in files:
        data = yaml.safe_load(file.read_text(encoding="utf-8")) or []
        items = data.get("cases") if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError(f"用例文件格式应为列表或含 cases: 的映射：{file}")
        for raw in items:
            if not isinstance(raw, dict):
                raise ValueError(f"用例条目应为映射：{file}")
            try:
                cases.append(build_case(raw))
            except ValueError as exc:
                raise ValueError(f"{file}: {exc}") from exc
    if not cases:
        raise ValueError(f"用例集为空：{target}")
    return cases


def build_input_text(case: EvalCase) -> str:
    """用例 → 喂给规划模型的输入。

    与 Django 侧同口径：默认直接给需求文本；`input: json` 时构造规格规定的四键中文 JSON
    （任务标题 / 任务目标 / 附件文本内容 / 设备ID），无 markdown 代码块包裹。
    """
    if case.input_kind != "json":
        return case.goal
    return json.dumps(
        {
            "任务标题": case.title,
            "任务目标": case.goal,
            "附件文本内容": case.attach,
            "设备ID": case.device,
        },
        ensure_ascii=False,
    )


# ── 机械校验（纯函数，可单测，零模型调用）──


def parse_plan(output: str) -> Plan | None:
    """模型输出 → Plan 契约对象（与生产同源：`_parse_json` + `_coerce`，失败即 None）。"""
    out = _parse_json(output or "")
    if not out:
        return None
    return _coerce(Plan, out.get("plan"))


def plan_text(plan: Plan) -> str:
    """Plan → 用于关键词覆盖比对的全文。"""
    parts = [plan.goal] + [f"{s.action} {s.assertion}" for s in plan.steps]
    return "\n".join(parts)


def check_contract(plan: Plan | None) -> list[str]:
    """硬性①：契约可解析、有步骤、每步 action 与 assert 非空。"""
    if plan is None:
        return ["输出不是合法的 plan 契约（JSON 不可解析或缺 plan）"]
    if not plan.steps:
        return ["plan.steps 为空"]
    issues = []
    for i, step in enumerate(plan.steps, 1):
        if not step.action.strip():
            issues.append(f"第 {i} 步 action 为空")
        if not step.assertion.strip():
            issues.append(f"第 {i} 步 assert 为空")
    return issues


def check_keywords(plan: Plan, keywords: list[str]) -> list[str]:
    """硬性②：用例登记的关键词必须全部出现在 plan 中。"""
    text = plan_text(plan)
    return [f"缺少关键词：{k}" for k in keywords if k and k not in text]


def check_steps_range(plan: Plan, steps_min: int, steps_max: int) -> list[str]:
    """硬性③：步骤数落在区间内。"""
    n = len(plan.steps)
    if n < steps_min or n > steps_max:
        return [f"步骤数 {n} 不在期望区间 [{steps_min}, {steps_max}]"]
    return []


def check_flow_tool(trace: list[dict], required: bool) -> list[str]:
    """硬性④：按提示词要求，规划前应调用页面流工具（可由用例关闭）。"""
    if not required:
        return []
    called = {
        str(row.get("name"))
        for row in trace or []
        if isinstance(row, dict) and row.get("type") == "call"
    }
    if "list_page_flows" not in called:
        return [f"未调用页面流工具 list_page_flows（实际调用：{sorted(called) or '无'}）"]
    return []


def check_mixed_log_check(plan: Plan, expected: bool) -> list[str]:
    """硬性⑤：声明该用例应混合取值时，log_check 不得是单一取值（检验标注区分度）。"""
    if not expected:
        return []
    values = {bool(step.log_check) for step in plan.steps}
    if len(values) < 2:
        return [f"log_check 取值无区分度（全为 {values.pop()}）"]
    return []


def suspect_multi_action(plan: Plan) -> list[str]:
    """疑似①：一个 action 里塞了多个副作用动作且出现并列连接词。"""
    found = []
    for i, step in enumerate(plan.steps, 1):
        action = step.action
        verbs = [v for v in SIDE_EFFECT_VERBS if v in action]
        if len(verbs) >= 2 and any(c in action for c in CONJUNCTIONS):
            found.append(f"疑似多动作：第 {i} 步「{action}」（命中动作 {verbs}）")
    return found


def suspect_empty_assert(plan: Plan) -> list[str]:
    """疑似②：断言是空话（不可观察）。"""
    found = []
    for i, step in enumerate(plan.steps, 1):
        hit = [p for p in EMPTY_ASSERT_PATTERNS if p in step.assertion]
        if hit:
            found.append(f"断言疑似空话：第 {i} 步「{step.assertion}」（命中 {hit}）")
    return found


def fingerprint(plan: Plan) -> str:
    """结构指纹：步骤数 + 每步命中的副作用动作（按序）。"""
    per_step = []
    for step in plan.steps:
        verbs = [v for v in SIDE_EFFECT_VERBS if v in step.action]
        per_step.append("+".join(verbs) or "-")
    return f"{len(plan.steps)}|" + "/".join(per_step)


def stability(fingerprints: list[str]) -> float | None:
    """稳定性 = 众数指纹占比；不足两次重复时返回 None（不适用）。"""
    if len(fingerprints) < 2:
        return None
    counts = {}
    for fp in fingerprints:
        counts[fp] = counts.get(fp, 0) + 1
    return max(counts.values()) / len(fingerprints)


def add_usage(total: dict, usage: dict) -> dict:
    """累加用量（输入 / 输出 / 缓存命中 / 缓存写入）。"""
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_input_tokens",
        "cache_creation_input_tokens",
    ):
        total[key] = int(total.get(key, 0)) + int((usage or {}).get(key, 0) or 0)
    return total


def encodable_text(text: str, encoding: str | None) -> str:
    """把当前输出编码无法表示的字符降级为 `?`。

    Windows 控制台默认 GBK，`✅` 这类字符会让 `stdout.write` 直接抛 UnicodeEncodeError
    （实测：模型调用已发生、报告却没写成）。控制台输出统一走这里；报告文件仍按 UTF-8 写。
    """
    enc = encoding or "utf-8"
    try:
        text.encode(enc)
        return text
    except UnicodeEncodeError:
        return text.encode(enc, errors="replace").decode(enc, errors="replace")
    except LookupError:
        # 编码名本身未知：退回 ascii 降级，保证"输出不抛错"这一条成立
        return text.encode("ascii", errors="replace").decode("ascii")


# ── 单次运行与结果 ──


@dataclass
class Attempt:
    """一次调用的结果。"""

    raw_output: str
    plan: Plan | None
    trace: list[dict]
    usage: dict
    cost: float
    seconds: float
    issues: list[str] = field(default_factory=list)
    suspects: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case: EvalCase
    attempts: list[Attempt]

    @property
    def passed(self) -> bool:
        """硬性项全部通过（疑似项不影响判定）。"""
        return bool(self.attempts) and all(not a.issues for a in self.attempts)

    @property
    def fingerprints(self) -> list[str]:
        return [fingerprint(a.plan) for a in self.attempts if a.plan is not None]

    @property
    def cost(self) -> float:
        return sum(a.cost for a in self.attempts)

    @property
    def seconds(self) -> float:
        return sum(a.seconds for a in self.attempts)


def run_case(case: EvalCase, planner, repeat: int) -> CaseResult:
    """跑一条用例（重复 repeat 次）；每次调用前清空上下文，与生产"每步清上下文"同口径。"""
    attempts: list[Attempt] = []
    for _ in range(max(1, repeat)):
        planner.reset_context()
        started = time.perf_counter()
        result = asyncio.run(planner.run(build_input_text(case)))
        seconds = time.perf_counter() - started

        plan = parse_plan(result.output)
        issues: list[str] = []
        issues += check_contract(plan)
        if plan is not None:
            issues += check_keywords(plan, case.must_contain)
            issues += check_steps_range(plan, case.steps_min, case.steps_max)
            issues += check_mixed_log_check(plan, case.expect_mixed_log_check)
        issues += check_flow_tool(result.tool_usage, case.require_flow_tool)

        suspects = []
        if plan is not None:
            suspects += suspect_multi_action(plan)
            suspects += suspect_empty_assert(plan)

        attempts.append(
            Attempt(
                raw_output=result.output or "",
                plan=plan,
                trace=list(result.tool_usage or []),
                usage=dict(result.usage or {}),
                cost=float(result.cost or 0.0),
                seconds=seconds,
                issues=issues,
                suspects=suspects,
            )
        )
    return CaseResult(case=case, attempts=attempts)


# ── 报告 ──


def render_report(
    *,
    tag: str,
    model_name: str,
    repeat: int,
    results: list[CaseResult],
    total_usage: dict,
    total_cost: float,
    total_seconds: float,
    started_at: datetime,
) -> str:
    """生成 Markdown 报告（汇总 + 逐用例明细 + plan 原文 + 工具轨迹）。"""
    passed = sum(1 for r in results if r.passed)
    stabilities = [s for s in (stability(r.fingerprints) for r in results) if s is not None]
    avg_stability = sum(stabilities) / len(stabilities) if stabilities else None
    lines = [
        f"# 规划模型能力评测报告 · {tag}",
        "",
        f"- 模型：`{model_name}`",
        f"- 用例数：{len(results)}，每条重复：{repeat} 次",
        f"- 开始时间：{started_at:%Y-%m-%d %H:%M:%S}",
        f"- 总耗时：{total_seconds:.1f}s",
        f"- 总费用：¥{total_cost:.6f}",
        (
            "- 总用量："
            f"输入 {total_usage.get('input_tokens', 0)} / "
            f"输出 {total_usage.get('output_tokens', 0)} / "
            f"缓存命中 {total_usage.get('cache_input_tokens', 0)}"
        ),
        "",
        "## 汇总",
        "",
        f"- 硬性通过：{passed}/{len(results)}",
        f"- 平均稳定性：{'不适用（未重复）' if avg_stability is None else f'{avg_stability:.0%}'}",
        "",
        "## 逐用例",
        "",
        "| 用例 | 硬性 | 步骤数 | 页面流工具 | 稳定性 | 费用(元) | 耗时(s) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        steps = "/".join(str(len(a.plan.steps)) if a.plan else "—" for a in r.attempts)
        flow_ok = all(not check_flow_tool(a.trace, True) for a in r.attempts)
        stab = stability(r.fingerprints)
        lines.append(
            f"| {r.case.id} | {'✅' if r.passed else '❌'} | {steps} | "
            f"{'✅' if flow_ok else '❌'} | "
            f"{'不适用' if stab is None else f'{stab:.0%}'} | {r.cost:.6f} | {r.seconds:.1f} |"
        )

    for r in results:
        lines += ["", f"### {r.case.id} — {r.case.title}", "", f"需求：`{r.case.goal}`", ""]
        for i, a in enumerate(r.attempts, 1):
            lines.append(f"**第 {i} 次**：{'通过' if not a.issues else '未通过'}")
            if a.issues:
                lines += [f"- ❌ {x}" for x in a.issues]
            if a.suspects:
                lines += [f"- ⚠️ {x}" for x in a.suspects]
            called = [
                f"{row.get('name')}({row.get('state')})"
                for row in a.trace
                if isinstance(row, dict) and row.get("type") == "call"
            ]
            lines.append(f"- 工具调用：{called or '无'}")
            lines.append(
                f"- 用量：输入 {a.usage.get('input_tokens', 0)} / 输出 {a.usage.get('output_tokens', 0)}"
                f" · 费用 ¥{a.cost:.6f} · 耗时 {a.seconds:.1f}s"
            )
            if a.plan is not None:
                lines += [
                    "",
                    "```json",
                    json.dumps(a.plan.model_dump(by_alias=True), ensure_ascii=False, indent=2),
                    "```",
                ]
            else:
                lines += ["", "模型原文（未解析出 plan）：", "", "```", a.raw_output[:2000], "```"]
    return "\n".join(lines) + "\n"


class Command(BaseCommand):
    help = "规划模型能力评测：批量跑用例 → 机械校验 → 控制台总表 + 报告（不走前端、不需设备）"

    def add_arguments(self, parser):
        parser.add_argument("--cases", required=True, help="用例 YAML 文件或目录")
        parser.add_argument("--repeat", type=int, default=1, help="每条用例重复次数（默认 1）")
        parser.add_argument("--model", default="", help="覆盖规划模型名（默认用平台配置）")
        parser.add_argument("--tag", default="", help="报告标签，默认取模型名")
        parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR, help="报告输出目录")

    def _say(self, text: str) -> None:
        """控制台输出（按当前输出编码降级，避免 GBK 控制台抛 UnicodeEncodeError）。"""
        self.stdout.write(encodable_text(text, getattr(self.stdout, "encoding", None)))

    def handle(self, *args, **options):
        try:
            cases = load_cases(options["cases"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        agent = get_platform_agent()
        if agent is None:
            raise CommandError("未找到平台智能体（先完成智能体配置）")

        config, planner, _executor, _verifier = build_device_models_for_agent(agent)
        override = (options["model"] or "").strip()
        if override:
            config.planner.model_name = override
            planner = build_device_models(
                config,
                build_tool_specs(),
                user_id=str(agent.owner_id or ""),
                skill_dirs=list_enabled_skill_dirs() if agent.enable_skills else [],
            )[0]

        model_name = config.planner.model_name
        repeat = max(1, int(options["repeat"]))
        tag = (options["tag"] or model_name or "planner").strip()

        self._say("=" * 72)
        self._say(f"规划模型评测：model={model_name} 用例数={len(cases)} 每条重复={repeat}")
        self._say("=" * 72)

        started_at = datetime.now()
        started = time.perf_counter()
        total_usage: dict = {}
        results: list[CaseResult] = []
        for case in cases:
            result = run_case(case, planner, case.repeat or repeat)
            results.append(result)
            for attempt in result.attempts:
                add_usage(total_usage, attempt.usage)
            mark = "[OK]  " if result.passed else "[FAIL]"
            steps = [len(a.plan.steps) if a.plan else "-" for a in result.attempts]
            self._say(
                f"{mark} {case.id:14} 步骤={steps} 费用={result.cost:.6f}元 耗时={result.seconds:.1f}s"
            )
            for attempt in result.attempts:
                for issue in attempt.issues:
                    self._say(f"       [FAIL] {issue}")
                for suspect in attempt.suspects:
                    self._say(f"       [WARN] {suspect}")
        total_seconds = time.perf_counter() - started
        total_cost = sum(r.cost for r in results)

        passed = sum(1 for r in results if r.passed)
        self._say("-" * 72)
        self._say(
            f"硬性通过 {passed}/{len(results)} · 总费用 {total_cost:.6f}元 · 总耗时 {total_seconds:.1f}s"
        )

        report = render_report(
            tag=tag,
            model_name=model_name,
            repeat=repeat,
            results=results,
            total_usage=total_usage,
            total_cost=total_cost,
            total_seconds=total_seconds,
            started_at=started_at,
        )
        report_dir = Path(options["report_dir"])
        report_dir.mkdir(parents=True, exist_ok=True)
        safe_tag = re.sub(r"[^0-9A-Za-z._-]+", "-", tag) or "planner"
        report_path = report_dir / f"{safe_tag}-{started_at:%Y%m%d-%H%M%S}.md"
        report_path.write_text(report, encoding="utf-8")
        self._say(f"报告：{report_path}")
