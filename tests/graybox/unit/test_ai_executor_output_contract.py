"""灰盒·单元测试 — 执行模型输出契约（spec: ai-executor-output）。

零外部依赖：只断言契约本身的三条口径 ——
1. 输出恰好三个字段 result / click_timer / screenshot，没有 action / message；
2. 无效输出（缺 result / 非 JSON 对象）不成契约（由调用方走 FAIL 兜底）；
3. 平台拼给验收模型的证据文本在无点击 / 未截图时如实标注，不编造值。
"""

from __future__ import annotations

from engines.ai.agentscope.workflow import ExecutionOutput, _coerce, _exec_evidence_text


def test_contract_has_exactly_three_fields() -> None:
    out = _coerce(
        ExecutionOutput,
        {"result": "PASS", "click_timer": "2026-09-28 17:01:12.645", "screenshot": "a/b.jpg"},
    )
    assert out is not None
    assert out.model_dump() == {
        "result": "PASS",
        "click_timer": "2026-09-28 17:01:12.645",
        "screenshot": "a/b.jpg",
    }


def test_read_only_step_keeps_two_evidence_fields_empty() -> None:
    out = _coerce(ExecutionOutput, {"result": "PASS"})
    assert out is not None
    assert out.click_timer == ""
    assert out.screenshot == ""


def test_invalid_output_is_rejected() -> None:
    assert _coerce(ExecutionOutput, {"click_timer": "t"}) is None  # 缺 result
    assert _coerce(ExecutionOutput, "PASS") is None  # 非 JSON 对象
    assert _coerce(ExecutionOutput, {"result": "OK"}) is None  # result 非 PASS/FAIL


def test_evidence_text_marks_missing_values() -> None:
    assert _exec_evidence_text(ExecutionOutput(result="PASS")) == (
        "点击前时间戳=本步无点击；点击后截图=本步未截图"
    )
    assert _exec_evidence_text(
        ExecutionOutput(result="PASS", click_timer="t1", screenshot="s1.jpg")
    ) == ("点击前时间戳=t1；点击后截图=s1.jpg")
