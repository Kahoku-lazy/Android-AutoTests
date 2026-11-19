"""需求拆解只接受边界和测试点，不生成用例任务。"""

from __future__ import annotations

import json

import pytest

from engines.backend_bridge.workflow.team_breakdown import run_team_breakdown

pytestmark = [pytest.mark.unit]


def test_missing_boundary_fails_whole_run():
    text = json.dumps([{"name": "开关", "test_points": "开和关", "out_of_scope": "配网"}])
    result = run_team_breakdown(text)
    assert result["passed"] is False
    assert result["modules"] == []
    assert result["created_followup"] is False


def test_valid_modules_keep_boundaries_only():
    text = json.dumps(
        [
            {
                "name": "开关",
                "boundary": "只覆盖电源",
                "test_points": "开、关",
                "out_of_scope": "配网",
            }
        ]
    )
    result = run_team_breakdown(text)
    assert result["passed"] is True
    assert result["module_count"] == 1
    assert "steps" not in result["modules"][0]
    assert result["created_followup"] is False
