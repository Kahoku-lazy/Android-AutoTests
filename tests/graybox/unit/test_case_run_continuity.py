"""一批用例的执行连续性：单条失败继续跑、结果区分清单、取消不追加失败。"""

from __future__ import annotations

import pytest

from engines.agents.role.config import RoleSpecConfig
from engines.agents.workflow.platform_run import (
    EXECUTOR_MAX_ITERS,
    VERIFIER_MAX_ITERS,
    run_platform_sop,
)

pytestmark = [pytest.mark.unit]

YAML_TEXT = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
- title: 乙
  steps:
    - action: 再点一下
      assert: 页面已切换
- title: 丙
  steps:
    - action: 收尾
      assert: 回到桌面
""".strip()


def _run(tmp_path, phases: dict[str, str]):
    """
    用替身跑一遍完整用例列表。

    Args:
        tmp_path: pytest 临时目录。
        phases: 用例标题 → 该条用例的阶段（completed / failed / cancelled）。

    Returns:
        (实际启动的用例标题列表, run_platform_sop 的返回字典)。
    """
    path = tmp_path / "cases.yaml"
    path.write_text(YAML_TEXT, encoding="utf-8")
    seen: list[str] = []

    def runner(title: str, steps: list[tuple[str, str]], opening: str) -> str:
        seen.append(title)
        return phases[title]

    result = run_platform_sop(
        str(path),
        "本次要操作的设备 serial 是：R5CT62RH88F。",
        executor_model=None,
        verifier_model=None,
        run_case=runner,
    )
    return seen, result


def test_failed_case_does_not_stop_the_batch(tmp_path):
    seen, result = _run(tmp_path, {"甲": "failed", "乙": "completed", "丙": "completed"})

    assert seen == ["甲", "乙", "丙"]
    assert result["status"] == "fail"
    assert result["completed"] == ["乙", "丙"]
    assert result["failed"] == ["甲"]
    assert "甲" in result["reason"]


def test_all_passed_leaves_no_failed_list(tmp_path):
    _, result = _run(tmp_path, {"甲": "completed", "乙": "completed", "丙": "completed"})

    assert result["status"] == "success"
    assert result["completed"] == ["甲", "乙", "丙"]
    assert result["failed"] == []
    assert result["reason"] == ""


def test_every_failed_case_is_named_in_reason(tmp_path):
    _, result = _run(tmp_path, {"甲": "failed", "乙": "completed", "丙": "failed"})

    assert result["failed"] == ["甲", "丙"]
    assert result["completed"] == ["乙"]
    assert "甲" in result["reason"] and "丙" in result["reason"]


def test_cancelled_case_stops_before_the_next(tmp_path):
    seen, result = _run(tmp_path, {"甲": "cancelled", "乙": "completed", "丙": "completed"})

    assert seen == ["甲"]
    assert result["status"] == "cancelled"
    assert result["failed"] == []


def test_cancel_keeps_earlier_failures(tmp_path):
    _, result = _run(tmp_path, {"甲": "failed", "乙": "cancelled", "丙": "completed"})

    assert result["status"] == "cancelled"
    assert result["failed"] == ["甲"]
    assert result["completed"] == []


def test_executor_budget_is_double_the_default():
    assert EXECUTOR_MAX_ITERS == 60
    assert VERIFIER_MAX_ITERS == 30
    assert RoleSpecConfig.__dataclass_fields__["max_iters"].default == 30
