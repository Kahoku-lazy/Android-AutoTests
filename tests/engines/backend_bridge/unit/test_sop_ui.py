"""平台 SOP 一次运行：结果字段、不打印、两次运行互不影响。

只测 `workflow/sop_ui.py` 的契约；用替身替换角色装配与 run_sop，不联网、不碰真机。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

import engines.backend_bridge.workflow.sop_ui as sop_ui

from engines.ae_harness.event import TokenUsage
from engines.ae_harness.middleware import ObservationMiddleware


@dataclass
class _StepOutcome:
    """替身：一步的结论（对齐 ae_harness 的 StepOutcome）。"""

    subject: str
    passed: bool
    attempts: int
    message: str = ""


def _usage() -> TokenUsage:
    """造一条真实用量记录（字段与事件层一致，不手搓替身）。"""
    return TokenUsage(
        api_key_env="GOVEE_API_KEY",
        round_index=1,
        started_at="2026-11-14_22-00-00.000",
        ended_at="2026-11-14_22-00-01.000",
        input_tokens=100,
        output_tokens=10,
        cache_input_tokens=60,
        cache_creation_input_tokens=0,
    )


@dataclass
class _Record:
    """替身：整轮记录。"""

    html_path: Path
    log_path: Path
    cost_s: float = 1.5
    usages: list = field(default_factory=lambda: [_usage()])


@dataclass
class _SopResult:
    """替身：run_sop 的返回值。"""

    phase: str = "done"
    steps: list = field(default_factory=lambda: [_StepOutcome("回到桌面", True, 1, "已在桌面")])
    record: object = None


@dataclass
class _Role:
    """替身：角色 bundle。"""

    name: str
    api_key_env: str = "GOVEE_API_KEY"

    class _Model:
        model = "deepseek-flash"

    class _Agent:
        def __init__(self, name: str) -> None:
            self.name = name
            self.model = _Role._Model()

    def __post_init__(self) -> None:
        """补一个带名字的 agent。"""
        self.agent = _Role._Agent(self.name)


@dataclass
class _Roles:
    """替身：装配结果。"""

    executor: _Role
    verifier: _Role
    observer: object


@pytest.fixture()
def fake_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """把角色装配与 run_sop 换成替身，并记录调用参数。"""
    calls: dict = {"runs": [], "role_instances": []}

    async def fake_build(*, model_short=None, observer=None, controls=None):
        del controls
        roles = _Roles(
            executor=_Role("ui_executor"),
            verifier=_Role("ui_verifier"),
            observer=observer or ObservationMiddleware(),
        )
        calls["role_instances"].append(roles)
        return roles

    async def fake_run_sop(executor, verifier, spec, **kwargs):
        calls["runs"].append({"spec": spec, "kwargs": kwargs})
        return _SopResult(
            record=_Record(html_path=tmp_path / "a.html", log_path=tmp_path / "a.jsonl")
        )

    monkeypatch.setattr(sop_ui, "build_sop_roles", fake_build)
    monkeypatch.setattr(sop_ui, "run_sop", fake_run_sop)
    return calls


async def test_result_carries_steps_and_usage(fake_run, tmp_path: Path):
    """返回值含阶段、每步结论、产物路径与四类 token。"""
    result = await sop_ui.run_sop_once("回到桌面", report_root=tmp_path)

    assert result.phase == "done"
    assert [(s.subject, s.passed, s.attempts) for s in result.steps] == [("回到桌面", True, 1)]
    assert result.report_path == tmp_path / "a.html"
    assert result.log_path == tmp_path / "a.jsonl"
    assert result.tokens == {"input": 100, "output": 10, "cache_hit": 60, "cache_creation": 0}
    assert result.by_api_key_env == {"GOVEE_API_KEY": 1}
    assert result.model == "deepseek-flash"
    assert len(result.usages) == 1


async def test_task_overrides_spec_but_steps_stay(fake_run, tmp_path: Path):
    """任务文本只覆盖 spec.task，步骤仍是 YAML 里的。"""
    await sop_ui.run_sop_once("打开设置", report_root=tmp_path)

    spec = fake_run["runs"][0]["spec"]
    assert spec.task == "打开设置"
    assert [step.subject for step in spec.steps], "步骤必须来自 YAML"


async def test_two_runs_build_new_roles(fake_run, tmp_path: Path):
    """两次运行各自新建角色，不复用上一轮实例。"""
    await sop_ui.run_sop_once("第一次", report_root=tmp_path)
    await sop_ui.run_sop_once("第二次", report_root=tmp_path)

    first, second = fake_run["role_instances"]
    assert first is not second
    assert first.executor is not second.executor


async def test_unknown_spec_key_raises(fake_run, tmp_path: Path):
    """未知流程键直接报错，不静默退回默认流程。"""
    with pytest.raises(KeyError):
        await sop_ui.run_sop_once("任务", spec_key="不存在", report_root=tmp_path)


async def test_run_prints_nothing(fake_run, tmp_path: Path, capsys):
    """运行入口不向标准输出写任何内容。"""
    await sop_ui.run_sop_once("回到桌面", report_root=tmp_path)

    captured = capsys.readouterr()
    assert captured.out == ""
