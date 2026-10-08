"""灰盒·单元测试 — 规划模型评测入口的机械判据（零模型调用、零网络）。

只测纯函数与用例加载：判据的"通过/不通过"两侧都覆盖；疑似项另测"不影响硬性判定"。
真实调用模型的那一遍由 `python manage.py planner_eval` 按需手动跑，不进本用例。
"""

import json

from pathlib import Path

import pytest

from apps.ai_assistant.management.commands.planner_eval import (
    EvalCase,
    add_usage,
    build_case,
    build_input_text,
    check_contract,
    check_flow_tool,
    check_keywords,
    check_mixed_log_check,
    check_steps_range,
    fingerprint,
    load_cases,
    parse_plan,
    render_report,
    stability,
    suspect_empty_assert,
    suspect_multi_action,
)
from engines.ai.workflow.workflow import Plan, Step

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def _plan(*steps: tuple[str, str, bool]) -> Plan:
    """构造桩 plan（契约里已不含 goal）。"""
    return Plan(steps=[Step(action=a, assertion=s, log_check=lc) for a, s, lc in steps])


# ── 契约解析 ──


def test_parse_plan_accepts_plain_and_fenced_json():
    plain = json.dumps(
        {"plan": {"goal": "g", "steps": [{"action": "启动 govee", "assert": "前台是 govee"}]}}
    )
    assert parse_plan(plain) is not None
    assert parse_plan(f"```json\n{plain}\n```") is not None


def test_parse_plan_rejects_invalid_output():
    assert parse_plan("") is None
    assert parse_plan("我不会") is None
    assert parse_plan('{"foo": 1}') is None
    assert parse_plan('{"plan": {"goal": "g", "steps": "不是列表"}}') is None


def test_parse_plan_ignores_legacy_goal_key():
    """契约已不含 goal：模型若仍输出该键，按 pydantic 默认行为忽略，解析照常成功。"""
    out = json.dumps(
        {
            "plan": {
                "goal": "打开 govee 应用并进入设备主页",
                "steps": [{"action": "启动 govee 应用", "assert": "前台是 govee"}],
            }
        }
    )
    plan = parse_plan(out)
    assert plan is not None
    assert "goal" not in plan.model_dump()
    assert len(plan.steps) == 1


# ── 硬性判据 ──


def test_check_contract_reports_missing_and_empty_fields():
    assert check_contract(None) == ["输出不是合法的 plan 契约（JSON 不可解析或缺 plan）"]
    assert check_contract(_plan()) == ["plan.steps 为空"]
    issues = check_contract(_plan(("  ", "", False)))
    assert any("action 为空" in x for x in issues)
    assert any("assert 为空" in x for x in issues)
    assert check_contract(_plan(("启动 govee", "前台是 govee", False))) == []


def test_check_keywords_hits_and_misses():
    plan = _plan(("进入 H6810 详情页", "页面标题显示 H6810", False))
    assert check_keywords(plan, ["H6810"]) == []
    assert check_keywords(plan, ["H6810", "音乐"]) == ["缺少关键词：音乐"]


def test_check_steps_range():
    plan = _plan(("a", "b", False))
    assert check_steps_range(plan, 1, 2) == []
    assert check_steps_range(plan, 2, 5) == ["步骤数 1 不在期望区间 [2, 5]"]


def test_check_flow_tool_requires_call_when_required():
    trace = [
        {"type": "call", "name": "list_page_flows"},
        {"type": "result", "name": "list_page_flows"},
    ]
    assert check_flow_tool(trace, True) == []
    assert check_flow_tool([], True) == ["未调用页面流工具 list_page_flows（实际调用：无）"]
    # 用例关闭该要求时不判失败
    assert check_flow_tool([], False) == []


def test_check_mixed_log_check_detects_no_distinction():
    uniform = _plan(("点开关", "开关关闭", True), ("回到首页", "首页可见", True))
    mixed = _plan(("点开关", "开关关闭", True), ("回到首页", "首页可见", False))
    assert check_mixed_log_check(uniform, True) != []
    assert check_mixed_log_check(mixed, True) == []
    # 未声明该期望时不判失败
    assert check_mixed_log_check(uniform, False) == []


# ── 疑似项（只提示、不判失败）──


def test_suspect_multi_action_flags_two_actions_with_conjunction():
    bad = _plan(("点击搜索框并输入 govee", "搜索框出现 govee", False))
    assert suspect_multi_action(bad)


def test_suspect_multi_action_allows_prompt_mandated_phrasing():
    """提示词规定的「先找到元素，再点击」句式不得被判疑似。"""
    good = _plan(("先在 APP主页找到「设备主页入口」元素，再点击该入口", "进入设备主页", False))
    assert suspect_multi_action(good) == []


def test_suspect_empty_assert_flags_boilerplate_but_not_observable():
    assert suspect_empty_assert(_plan(("点击开关", "操作成功", False)))
    assert (
        suspect_empty_assert(_plan(("启动 govee 应用", "应用启动成功并停留在 APP主页", False)))
        == []
    )


# ── 稳定性与用量 ──


def test_fingerprint_and_stability():
    p1 = _plan(("启动 govee 应用", "前台是 govee", False), ("点击设备入口", "进入设备页", False))
    p2 = _plan(("启动 govee", "前台是 govee", False), ("点击设备入口", "进入设备页", False))
    p3 = _plan(("启动 govee 应用", "前台是 govee", False))
    assert fingerprint(p1) == fingerprint(p2)
    assert fingerprint(p1) != fingerprint(p3)
    assert stability([fingerprint(p1), fingerprint(p2)]) == 1.0
    assert stability([fingerprint(p1), fingerprint(p3)]) == 0.5
    assert stability([fingerprint(p1)]) is None  # 未重复 → 不适用


def test_add_usage_accumulates_all_fields():
    total = add_usage({}, {"input_tokens": 10, "output_tokens": 2, "cache_input_tokens": 3})
    total = add_usage(
        total, {"input_tokens": 5, "output_tokens": 1, "cache_creation_input_tokens": 7}
    )
    assert total == {
        "input_tokens": 15,
        "output_tokens": 3,
        "cache_input_tokens": 3,
        "cache_creation_input_tokens": 7,
    }


def test_encodable_text_degrades_unsupported_chars():
    """回归：Windows GBK 控制台下 emoji 会让 stdout.write 抛 UnicodeEncodeError。"""
    from apps.ai_assistant.management.commands.planner_eval import encodable_text

    assert encodable_text("纯中文 OK", "gbk") == "纯中文 OK"
    degraded = encodable_text("[OK] 步骤与费用", "gbk")
    assert degraded == "[OK] 步骤与费用"
    # ✅ 在 GBK 下不可编码 → 降级为 ?，而不是抛错
    assert "?" in encodable_text("✅ 通过", "gbk")
    # 未知编码名不抛错（回退为可写文本）
    assert encodable_text("✅ 通过", "no-such-encoding")


# ── 用例加载与输入构造 ──


def test_build_case_validates_required_fields():
    case = build_case({"id": "c1", "goal": "打开 govee 应用"})
    assert case.input_kind == "text" and case.require_flow_tool is True
    with pytest.raises(ValueError, match="缺少 id"):
        build_case({"goal": "x"})
    with pytest.raises(ValueError, match="goal 为空"):
        build_case({"id": "c2"})
    with pytest.raises(ValueError, match="只能是 text 或 json"):
        build_case({"id": "c3", "goal": "x", "input": "xml"})
    with pytest.raises(ValueError, match="steps_min 大于 steps_max"):
        build_case({"id": "c4", "goal": "x", "expect": {"steps_min": 5, "steps_max": 2}})


def test_build_input_text_plain_and_four_key_json():
    plain = EvalCase(id="c", title="t", goal="打开 govee 应用")
    assert build_input_text(plain) == "打开 govee 应用"

    as_json = EvalCase(
        id="c",
        title="进设备页",
        goal="打开 govee 应用并进入设备主页",
        input_kind="json",
        attach="附件说明",
        device="RF8N21MSW7A",
    )
    payload = json.loads(build_input_text(as_json))
    assert payload == {
        "任务标题": "进设备页",
        "任务目标": "打开 govee 应用并进入设备主页",
        "附件文本内容": "附件说明",
        "设备ID": "RF8N21MSW7A",
    }


def test_load_cases_from_file_and_dir(tmp_path):
    one = tmp_path / "a.yaml"
    one.write_text(
        "cases:\n"
        "  - id: c1\n"
        "    goal: 打开 govee 应用\n"
        "    expect: {must_contain: [govee], steps_min: 1, steps_max: 3}\n",
        encoding="utf-8",
    )
    cases = load_cases(one)
    assert [c.id for c in cases] == ["c1"]
    assert cases[0].must_contain == ["govee"] and cases[0].steps_max == 3

    # 目录形式（多文件合并）
    second = tmp_path / "b.yaml"
    second.write_text("cases:\n  - id: c2\n    goal: 启动应用\n", encoding="utf-8")
    assert [c.id for c in load_cases(tmp_path)] == ["c1", "c2"]

    bad = tmp_path / "bad.yaml"
    bad.write_text("cases:\n  - goal: 没有 id\n", encoding="utf-8")
    with pytest.raises(ValueError, match="缺少 id"):
        load_cases(bad)


def test_load_cases_rejects_missing_path_and_empty(tmp_path):
    with pytest.raises(ValueError, match="用例路径不存在"):
        load_cases(tmp_path / "nope.yaml")
    empty = tmp_path / "empty.yaml"
    empty.write_text("cases: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="用例集为空"):
        load_cases(empty)


def test_committed_case_files_match_agreed_scope():
    """口径守卫：正式用例集只有单步与多步两条；更难的场景在 extended.yaml 按需跑。"""
    cases_dir = Path(__file__).resolve().parents[3] / "tests" / "ai_planner" / "cases"

    main = load_cases(cases_dir / "planner.yaml")
    assert [c.id for c in main] == ["single-step", "multi-step"], (
        f"正式口径应为单步 + 多步两条，实际：{[c.id for c in main]}"
    )

    extended = load_cases(cases_dir / "extended.yaml")
    assert len(extended) >= 5, f"扩展用例数骤降：{[c.id for c in extended]}"
    assert not ({c.id for c in main} & {c.id for c in extended}), "两个文件不应重复用例"


# ── 报告 ──


def test_render_report_contains_summary_and_case_details():
    from datetime import datetime

    from apps.ai_assistant.management.commands.planner_eval import Attempt, CaseResult

    case = EvalCase(id="c1", title="单步", goal="打开 govee 应用")
    plan = _plan(("启动 govee 应用", "前台是 govee 首页", False))
    attempt = Attempt(
        raw_output="{}",
        plan=plan,
        trace=[{"type": "call", "name": "list_page_flows"}],
        usage={"input_tokens": 100, "output_tokens": 10, "cache_input_tokens": 0},
        cost=0.0001,
        seconds=1.5,
        issues=[],
        suspects=["疑似多动作：示例"],
    )
    report = render_report(
        tag="unit",
        model_name="stub-model",
        repeat=1,
        results=[CaseResult(case=case, attempts=[attempt])],
        total_usage={"input_tokens": 100, "output_tokens": 10, "cache_input_tokens": 0},
        total_cost=0.0001,
        total_seconds=1.5,
        started_at=datetime(2026, 10, 8, 12, 0, 0),
    )
    assert "# 规划模型能力评测报告 · unit" in report
    assert "硬性通过：1/1" in report
    assert "stub-model" in report
    assert "### c1 — 单步" in report
    assert "疑似多动作：示例" in report
    assert '"action": "启动 govee 应用"' in report
