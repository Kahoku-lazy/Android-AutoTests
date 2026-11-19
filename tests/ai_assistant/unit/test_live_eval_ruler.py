"""四条发布规则：未勾选、验收者写操作、连续重复、实例变化。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.services.live_rulers import grade_process

pytestmark = [pytest.mark.unit]

ALLOWED = {"adb_tap", "adb_dump_ui"}


def test_live_eval_ruler_names_unseen_and_verifier_write():
    failures = grade_process(
        [
            {"role": "executor", "tool": "adb_install", "input": {}},
            {"role": "verifier", "tool": "adb_tap", "input": {}},
        ],
        allowed=ALLOWED,
    )
    texts = [item["text"] for item in failures]
    assert any("adb_install" in text for text in texts)
    assert any("adb_tap" in text for text in texts)
    assert "score" not in failures[0]


def test_live_eval_ruler_repeat_stops_at_verifier():
    repeated = grade_process(
        [
            {"role": "executor", "tool": "adb_tap", "input": {"nx": 1}},
            {"role": "executor", "tool": "adb_tap", "input": {"nx": 1}},
        ],
        allowed=ALLOWED,
    )
    separated = grade_process(
        [
            {"role": "executor", "tool": "adb_tap", "input": {"nx": 1}},
            {"role": "verifier", "tool": "adb_dump_ui", "input": {}},
            {"role": "executor", "tool": "adb_tap", "input": {"nx": 1}},
        ],
        allowed=ALLOWED,
    )
    assert repeated[0]["ruler"] == "repeat"
    assert separated == []


def test_live_eval_ruler_flags_changed_instance_only():
    assert grade_process([], allowed=ALLOWED, same_instance=False)[0]["ruler"] == "instance"
    assert grade_process([], allowed=ALLOWED, same_instance=True) == []
