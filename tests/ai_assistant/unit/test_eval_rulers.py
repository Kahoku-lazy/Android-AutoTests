"""评测尺子：驳回次数、空阶段、连续重复，以及中间隔着验收不算重复。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.services.eval_rulers import grade
from backend.apps.ai_assistant.services.eval_samples import sample_ids

pytestmark = [pytest.mark.unit]


def test_sample_ids_match_between_page_and_pytest():
    assert sample_ids() == ["A1", "S1", "S2", "S3"]


def test_eval_ruler_attempt_mismatch_names_the_step():
    failures = grade(
        {"phase": "COMPLETED", "steps": [{"subject": "回到桌面", "passed": True, "attempts": 1}]},
        {"phase": "COMPLETED", "steps": [{"subject": "回到桌面", "passed": True, "attempts": 2}]},
    )
    assert failures[0]["subject"] == "回到桌面"
    assert "2" in failures[0]["text"]
    assert "1" in failures[0]["text"]
    assert "score" not in failures[0]


def test_eval_ruler_skips_missing_phase():
    assert (
        grade(
            {"same_instance": True, "tools": []},
            {"same_instance": True, "unseen_tools": ["adb_tap"]},
        )
        == []
    )


def test_eval_ruler_flags_consecutive_repeat_but_not_separated_calls():
    repeated = grade({"repeated": True}, {"repeat": True})
    separated = grade({"repeated": False}, {"repeat": True})
    assert repeated[0]["ruler"] == "repeat"
    assert separated == []


def test_eval_ruler_names_verifier_write_tool():
    failures = grade({"verifier_tools": ["adb_tap"]}, {"verifier_write_tools": []})
    assert failures[0]["text"].endswith("adb_tap")
