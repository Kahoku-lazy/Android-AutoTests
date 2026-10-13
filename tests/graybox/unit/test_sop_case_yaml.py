"""手工入口从 YAML 读出一条或多条用例，每条单独装配。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


def test_list_root_keeps_title_and_step_order(tmp_path: Path) -> None:
    """根为单条列表时，标题和两步顺序原样装入，重试上限为 2。"""
    from engines.agents.agents import build_case_sops

    path = tmp_path / "case.yaml"
    path.write_text(
        "- title: H6810 详情页开关测试\n"
        "  steps:\n"
        "    - action: 点击H6810开关按键\n"
        "      assert: 断言设备日志关闭设备成功\n"
        "    - action: 再次点击H6810开关按键\n"
        "      assert: 断言设备日志打开设备成功\n",
        encoding="utf-8",
    )
    sop = build_case_sops(_Role(_Agent()), _Role(_Agent()), path)[0]
    assert sop.name == "H6810 详情页开关测试"
    assert [step.subject for step in sop.steps] == [
        "点击H6810开关按键",
        "再次点击H6810开关按键",
    ]
    assert [step.description for step in sop.steps] == [
        "断言设备日志关闭设备成功",
        "断言设备日志打开设备成功",
    ]
    assert sop.steps[0].max_attempts == 2


def test_mapping_root_is_one_case(tmp_path: Path) -> None:
    """根为单个映射时同样装成一步。"""
    from engines.agents.agents import build_case_sops

    path = tmp_path / "case.yaml"
    path.write_text(
        "title: 单步\nsteps:\n  - action: 点按键\n    assert: 日志关闭成功\n",
        encoding="utf-8",
    )
    sop = build_case_sops(_Role(_Agent()), _Role(_Agent()), path)[0]
    assert sop.name == "单步"
    assert sop.steps[0].subject == "点按键"
    assert sop.steps[0].description == "日志关闭成功"


def test_two_cases_assemble_in_order(tmp_path: Path) -> None:
    """一个文件里的两条用例按顺序各装配成一份流程。"""
    from engines.agents.agents import build_case_sops

    path = tmp_path / "two.yaml"
    path.write_text(
        "- title: 甲\n  steps:\n    - action: 做甲\n      assert: 验甲\n"
        "- title: 乙\n  steps:\n    - action: 做乙\n      assert: 验乙\n",
        encoding="utf-8",
    )
    sops = build_case_sops(_Role(_Agent()), _Role(_Agent()), path)
    assert [sop.name for sop in sops] == ["甲", "乙"]
    assert sops[0].steps[0].subject == "做甲"
    assert sops[1].steps[0].description == "验乙"
    assert sops[0].steps[0].max_attempts == 2
    assert sops[1].steps[0].max_attempts == 2


def test_unusable_case_files_are_refused(tmp_path: Path) -> None:
    """缺断言、空白动作、文件不存在都在装配前失败。"""
    from engines.agents.agents import build_case_sops

    missing_assert = tmp_path / "missing.yaml"
    missing_assert.write_text(
        "title: 缺断言\nsteps:\n  - action: 点按键\n",
        encoding="utf-8",
    )
    blank_action = tmp_path / "blank.yaml"
    blank_action.write_text(
        "title: 空白\nsteps:\n  - action: '   '\n    assert: 验一下\n",
        encoding="utf-8",
    )
    role = _Role(_Agent())
    for path in (missing_assert, blank_action, tmp_path / "nope.yaml"):
        with pytest.raises(ValueError):
            build_case_sops(role, role, path)


def test_final_summary_is_pass_when_every_case_completes() -> None:
    """两条都完成时汇总为 PASS，并加总 token 与费用。"""
    from engines.agents.agents import final_summary

    text = final_summary(
        12.5,
        [_report(1, 10, 2, 0.1), _report(2, 3, 4, 0.2)],
        [
            ("甲", "completed", [_row("completed", True, "")]),
            ("乙", "completed", [_row("completed", True, "")]),
        ],
    )
    assert "甲：PASS" in text
    assert "乙：PASS" in text
    assert "FAIL" not in text
    assert "失败点" not in text
    assert "12.50 秒" in text
    assert "模型调用 3 次" in text
    assert "输入 13" in text
    assert "输出 6" in text
    assert "合计 0.3 元" in text


def test_final_summary_lists_the_failed_step() -> None:
    """未完成的用例标 FAIL，并写出失败的那一步，未开始的后续步骤不算失败点。"""
    from engines.agents.agents import final_summary

    text = final_summary(
        3,
        [_report(1, 1, 1, 0.01)],
        [
            (
                "短卡片",
                "failed",
                [
                    _row("completed", True, ""),
                    _row("failed", False, "没看到样式栏"),
                    _row("pending", None, ""),
                ],
            )
        ],
    )
    assert "短卡片：FAIL" in text
    assert "第 2 步 点按键：没看到样式栏" in text
    assert "第 3 步" not in text


def test_final_summary_marks_each_case() -> None:
    """一条失败、一条成功时，各自用标题带上 PASS 或 FAIL，失败点只挂在失败用例下。"""
    from engines.agents.agents import final_summary

    text = final_summary(
        8,
        [_report(1, 1, 1, 0.01), _report(1, 2, 2, 0.02)],
        [
            ("H6810 短卡片页开关测试", "failed", [_row("failed", False, "没看到样式栏")]),
            ("H6810 详情页亮度、颜色与场景模式测试", "completed", [_row("completed", True, "")]),
        ],
    )
    assert "H6810 短卡片页开关测试：FAIL" in text
    assert "H6810 详情页亮度、颜色与场景模式测试：PASS" in text
    fail_at = text.index("H6810 短卡片页开关测试：FAIL")
    pass_at = text.index("H6810 详情页亮度、颜色与场景模式测试：PASS")
    point_at = text.index("没看到样式栏")
    assert fail_at < point_at < pass_at


def _row(phase: str, passed: bool | None, message: str) -> dict:
    return {
        "subject": "点按键",
        "phase": phase,
        "passed": passed,
        "message": message,
        "verifier": "verifier",
    }


def _report(calls: int, input_tokens: int, output_tokens: int, total_cost: float) -> dict:
    return {
        "calls": calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_hit_tokens": 0,
        "total_cost": total_cost,
    }


def test_missing_cli_path_explains_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """不传路径时退出并打印用法，不进入装配。"""
    from engines.agents.agents import parse_case_args

    with pytest.raises(SystemExit) as caught:
        parse_case_args([])
    assert caught.value.code != 0
    assert "case" in capsys.readouterr().err


class _Role:
    def __init__(self, agent) -> None:
        self.agent = agent


class _Agent:
    name = "stub"
