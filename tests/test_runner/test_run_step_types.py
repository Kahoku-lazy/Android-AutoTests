"""run-step 步骤类型白名单单测（fix-run-step-step-types：真机发现 #3 回归保护）。"""

import pytest

from apps.test_runner.views.task_views import KNOWN_STEP_TYPES

pytestmark = [pytest.mark.unit, pytest.mark.test_runner]

NEW_ADB_TYPES = [
    "adb_start_app",
    "adb_kill_app",
    "adb_perf_element_time",
    "adb_wait_toast",
    "adb_if_appear",
    "adb_if_disappear",
    "adb_loop_n",
    "adb_loop_elements",
    "adb_poll_text",
]

LEGACY_TYPES = [
    "start_app",
    "kill_app",
    "perf_element_time",
    "wait_toast",
    "if_element_appear",
    "if_element_disappear",
    "loop_n",
    "loop_elements",
]


class TestKnownStepTypes:
    def test_new_adb_types_included(self):
        assert all(t in KNOWN_STEP_TYPES for t in NEW_ADB_TYPES)

    def test_legacy_types_still_supported(self):
        assert all(t in KNOWN_STEP_TYPES for t in LEGACY_TYPES)

    def test_unknown_type_excluded(self):
        assert "definitely_not_a_step" not in KNOWN_STEP_TYPES
