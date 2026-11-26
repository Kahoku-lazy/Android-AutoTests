import re

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ENGINES = ROOT / "engines"
BOUND_SOP = ENGINES / "backend_bridge" / "workflow" / "bound_sop.py"
BOUND_ROLES = ENGINES / "backend_bridge" / "workflow" / "bound_roles.py"
SESSION = ENGINES / "backend_bridge" / "session.py"
RUN_PARAMS = ENGINES / "backend_bridge" / "agents" / "run_params.py"
RUNNER = ENGINES / "ae_harness" / "workflow" / "sop" / "runner.py"
ALIGNED = ENGINES / "ae_harness" / "event" / "aligned.py"
RENDER = ENGINES / "ae_harness" / "event" / "render_aligned.py"
TASK_RUNNER = ROOT / "backend" / "apps" / "task_list" / "task_runner.py"

pytestmark = [pytest.mark.unit, pytest.mark.arch]


class TestSopDeviceContract:
    def test_device_is_checked_before_roles_are_built(self):
        content = BOUND_SOP.read_text(encoding="utf-8")
        check = content.index("require_online(serial)")
        build = content.index("build_bound_roles(")
        assert check < build, "设备校验必须在装配角色之前"

    def test_serial_is_held_for_the_whole_run(self):
        content = BOUND_SOP.read_text(encoding="utf-8")
        assert "serial_lock(" in content
        assert content.index("serial_lock(") < content.index("await run_sop(")

    def test_guard_is_shared_with_single_role_path(self):
        assert "require_online" in SESSION.read_text(encoding="utf-8")
        guard = (ENGINES / "backend_bridge" / "device_guard.py").read_text(encoding="utf-8")
        assert "def require_online(" in guard
        assert "def serial_lock(" in guard


class TestSopObservationContract:
    def test_sop_captures_full_messages(self):
        content = BOUND_SOP.read_text(encoding="utf-8")
        assert "capture_messages=True" in content

    def test_middleware_takes_the_switch(self):
        content = BOUND_ROLES.read_text(encoding="utf-8")
        assert "ObservationMiddleware(capture_messages=capture_messages)" in content

    def test_two_paths_share_run_params(self):
        params = RUN_PARAMS.read_text(encoding="utf-8")
        for name in ("MAX_IMAGE_NUM", "TOOL_RESULT_LIMIT", "MAX_ITERS"):
            assert f"{name} = " in params, f"缺 {name}"
        assert "apply_run_params" in SESSION.read_text(encoding="utf-8")
        assert "apply_run_params" in BOUND_ROLES.read_text(encoding="utf-8")


class TestSopRunnerOutlets:
    def test_runner_exposes_outlets_and_render_switch(self):
        content = RUNNER.read_text(encoding="utf-8")
        for name in ("on_begin", "on_event", "on_observation", "render_report"):
            assert f"{name}:" in content, f"run_sop 缺 {name}"
        assert "on_begin(recorder)" in content
        assert "if render_report:" in content

    def test_runner_forwards_events_and_observations(self):
        content = RUNNER.read_text(encoding="utf-8")
        assert "on_event(event)" in content
        assert "observation_sink=on_observation" in content


class TestSopReportContract:
    def test_record_carries_steps_and_roles(self):
        content = ALIGNED.read_text(encoding="utf-8")
        assert 'payload["steps"] = list(self._steps)' in content
        assert "bind_step_reply" in content
        assert 'row["role"] = role' in content

    def test_report_splits_stage_by_step(self):
        content = RENDER.read_text(encoding="utf-8")
        assert "_stage_steps" in content
        assert "_reply_rounds" in content
        assert "第 {position} 步" in content

    def test_report_marks_failed_step(self):
        content = RENDER.read_text(encoding="utf-8")
        assert "未通过" in content
        assert "步骤结论" in content

    def test_single_role_still_groups_by_round(self):
        content = RENDER.read_text(encoding="utf-8")
        assert re.search(r'if parts\["steps"\]\s*:\s*\n\s*return self\._stage_steps', content)
        assert "按轮次分阶段" in content


class TestFailureReportContract:
    def test_bound_sop_renders_abort_report(self):
        content = BOUND_SOP.read_text(encoding="utf-8")
        assert "on_abort" in content
        assert "def abort(" in content
        assert "运行中断" in content

    def test_runner_links_failure_report(self):
        content = TASK_RUNNER.read_text(encoding="utf-8")
        assert "_report_locator(report_path)" in content
        assert "on_abort=_remember" in content
