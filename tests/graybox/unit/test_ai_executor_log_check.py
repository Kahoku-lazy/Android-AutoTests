"""灰盒·单元测试 — 执行侧点击证据（spec: ai-executor-log-check）。

零外部依赖：只断言纯函数的配对与门控口径 ——
1. 每次副作用点击给出「点击前时间点 + 点击后截图路径」，一步多次点击各自成条；
2. 截图只认该次点击**之后**的第一张，且不重复分配；其后无截图则留空；
3. 只读步骤不产出条目；上一步遗留的工具返回被切片排除；
4. `need_log` 为假时即使有证据也不附日志；为真时附同一份证据；
5. 过程记录只在「有点击或带日志」时写 executor_log_check 键。
"""

from __future__ import annotations

import json

from types import SimpleNamespace

from engines.ai.agentscope.logcheck import build_executor_log_check
from engines.ai.agentscope.workflow import (
    ExecutionOutput,
    Step,
    VerificationOutput,
    _log_step,
)

CLICK_1 = "2026-09-28 17:01:12.645"
CLICK_2 = "2026-09-28 17:01:15.000"
SHOT_1 = "ai_tasks/12/s2_l1.jpg"
SHOT_2 = "ai_tasks/12/s2_l2.jpg"

EVIDENCE = {
    "conclusion": "hit",
    "threshold_seconds": 5.0,
    "window_line_count": 1,
    "hits": [{"keyword": "switch_off", "grade": "strong", "count": 1}],
}


def _click_row(action_time: str = CLICK_1, name: str = "click_ratio") -> dict:
    return {
        "type": "result",
        "name": name,
        "output": json.dumps({"package": "com.demo", "action_time": action_time}),
    }


def _shot_row(path: str = SHOT_1) -> dict:
    return {"type": "result", "name": "screenshot_page", "output": "{}", "screenshot_path": path}


def _role(rows: list[dict]) -> SimpleNamespace:
    return SimpleNamespace(tool_usage=rows, thinking=[], output="{}", screenshot_path="")


def test_step_log_check_defaults_false_and_parses_true() -> None:
    plain = Step(action="点击开关", assertion="页面出现已开启")
    marked = Step(action="点击开关", assertion="设备上报 switch_off", log_check=True)
    assert plain.log_check is False
    assert marked.log_check is True


def test_step_log_check_never_sinks_the_plan() -> None:
    """取值奇怪（字符串 / 数字 / 空）时宽松归一为布尔，不让整步建模失败。"""
    cases = [("true", True), ("是", True), (1, True), ("no", False), (0, False), (None, False)]
    for raw, expected in cases:
        step = Step(action="点击开关", assertion="设备上报 switch_off", log_check=raw)
        assert step.log_check is expected, raw
    # 真正无法解读的对象按「不需日志核对」处理
    assert Step(action="a", assertion="b", log_check={"x": 1}).log_check is False


def test_single_click_pairs_with_following_screenshot() -> None:
    block = build_executor_log_check(_role([_click_row(), _shot_row()]))
    assert block["clicks"] == [{"action_time": CLICK_1, "screenshot_path": SHOT_1}]
    assert block["log"] is None


def test_multiple_clicks_pair_in_order() -> None:
    rows = [_click_row(), _shot_row(SHOT_1), _click_row(CLICK_2), _shot_row(SHOT_2)]
    block = build_executor_log_check(_role(rows))
    assert block["clicks"] == [
        {"action_time": CLICK_1, "screenshot_path": SHOT_1},
        {"action_time": CLICK_2, "screenshot_path": SHOT_2},
    ]


def test_click_without_following_screenshot_stays_empty() -> None:
    block = build_executor_log_check(_role([_click_row()]))
    assert block["clicks"] == [{"action_time": CLICK_1, "screenshot_path": ""}]


def test_screenshot_before_click_is_not_reused() -> None:
    """截图必须晚于点击：点击之前的截图不算该次点击的证据。"""
    block = build_executor_log_check(_role([_shot_row(SHOT_1), _click_row()]))
    assert block["clicks"][0]["screenshot_path"] == ""


def test_one_screenshot_serves_only_the_first_click() -> None:
    """一张截图不能同时证明两次点击：第二次点击如实留空。"""
    block = build_executor_log_check(_role([_click_row(), _click_row(CLICK_2), _shot_row()]))
    assert [item["screenshot_path"] for item in block["clicks"]] == [SHOT_1, ""]


def test_read_only_step_yields_no_click() -> None:
    rows = [{"type": "result", "name": "current_app", "output": '{"package": "com.demo"}'}]
    block = build_executor_log_check(_role(rows))
    assert block["clicks"] == []


def test_previous_step_results_are_skipped() -> None:
    rows = [_click_row(), _shot_row(), _click_row(CLICK_2), _shot_row(SHOT_2)]
    block = build_executor_log_check(_role(rows), skip_results=2)
    assert block["clicks"] == [{"action_time": CLICK_2, "screenshot_path": SHOT_2}]
    assert build_executor_log_check(_role(rows), skip_results=4)["clicks"] == []


def test_log_only_attached_when_step_needs_it() -> None:
    rows = [_click_row(), _shot_row()]
    without = build_executor_log_check(_role(rows), log_evidence=EVIDENCE, need_log=False)
    with_log = build_executor_log_check(_role(rows), log_evidence=EVIDENCE, need_log=True)
    assert without["log"] is None
    assert with_log["log"] == EVIDENCE


def test_need_log_without_evidence_stays_empty() -> None:
    block = build_executor_log_check(_role([_click_row()]), log_evidence=None, need_log=True)
    assert block["log"] is None


def _step_entry(block: dict | None) -> dict:
    return _log_step(
        Step(action="点击开关", assertion="设备上报 switch_off"),
        1,
        ExecutionOutput(result="PASS", click_timer=CLICK_1, screenshot=SHOT_1),
        VerificationOutput(
            result="PASS", click_timer=CLICK_1, screenshot=SHOT_1, actual="日志命中"
        ),
        executor_log_check=block,
    )


def test_log_step_writes_key_when_block_has_content() -> None:
    entry = _step_entry(
        {"clicks": [{"action_time": CLICK_1, "screenshot_path": SHOT_1}], "log": None}
    )
    assert entry["executor_log_check"]["clicks"][0]["action_time"] == CLICK_1


def test_log_step_omits_key_for_empty_block() -> None:
    assert "executor_log_check" not in _step_entry({"clicks": [], "log": None})
    assert "executor_log_check" not in _step_entry(None)
