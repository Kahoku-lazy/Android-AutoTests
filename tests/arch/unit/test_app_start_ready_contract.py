import inspect
import re

from pathlib import Path

import pytest

from engines.ae_harness.tools.adb import tools as adb_tools

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "engines" / "ae_harness" / "tools" / "adb" / "tools.py"
SESSION = ROOT / "engines" / "backend_bridge" / "session.py"

pytestmark = [pytest.mark.unit, pytest.mark.arch]


class TestAppStartDefaults:
    def test_waits_for_ready_by_default(self):
        params = inspect.signature(adb_tools.adb_app_start).parameters
        assert params["wait_ready"].default is True
        assert params["with_screen"].default is False
        assert float(params["timeout_s"].default) == 12.0
        assert int(params["settle_ms"].default) == 1200

    def test_returns_union_of_chunk_and_text(self):
        annotation = str(inspect.signature(adb_tools.adb_app_start).return_annotation)
        assert "ToolChunk" in annotation and "str" in annotation

    def test_tool_count_is_unchanged(self):
        assert len(adb_tools.build_adb_tools()) == 16
        assert len(adb_tools.build_adb_tools(include_devices=False)) == 15


class TestAppStartBehaviourSource:
    def test_timeout_does_not_raise(self):
        content = TOOLS.read_text(encoding="utf-8")
        assert '"timed_out": True' in content
        assert '"ready": False' in content

    def test_first_screen_reuses_screenshot_impl(self):
        content = TOOLS.read_text(encoding="utf-8")
        assert "_screenshot_with_points(" in content
        start = content.index("def adb_app_start(")
        end = content.index("def adb_app_stop(")
        body = content[start:end]
        assert "_screenshot_with_points(" in body
        assert "with_screen" in body

    def test_wait_can_be_switched_off(self):
        content = TOOLS.read_text(encoding="utf-8")
        assert "if wait_ready:" in content

    def test_front_component_read_once(self):
        content = TOOLS.read_text(encoding="utf-8")
        assert content.count('"dumpsys", "activity", "activities"') == 1
        assert "def _resumed_component(" in content
        assert re.search(r"def _front_package\(.*?\n(?:.*\n)*?\s+return component\.split", content)


class TestReadyPromptContract:
    def test_prompt_mentions_ready_signal(self):
        content = SESSION.read_text(encoding="utf-8")
        assert "启动就绪规则" in content
        assert "with_screen" in content
        assert "ready=true" in content

    def test_single_role_prompt_still_carries_serial_and_shot_hints(self):
        content = SESSION.read_text(encoding="utf-8")
        for marker in ("_SERIAL_PREFIX", "_SERIAL_HINT", "_SHOT_HINT", "_READY_HINT"):
            assert marker in content
