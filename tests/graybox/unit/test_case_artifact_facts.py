"""事实预检：出处真实、引用完整、数值可追溯；覆盖率只告警。"""

from __future__ import annotations

from engines.agents.workflow.case_artifact import (
    Artifact,
    ArtifactBoundary,
    ArtifactCase,
    ArtifactScenario,
    ArtifactState,
    ArtifactStep,
    ArtifactTransition,
)
from engines.agents.workflow.case_artifact_facts import (
    check_artifact_facts,
    format_facts,
)

REQUIREMENT = (
    "打开 App 后进入设备详情页，顶栏显示型号与连接状态。"
    "点击场景模式后进入场景页，页面显示 Nature 与 Festival 两个标签。"
    "名称最多 22 个字符，超出时提示过长。"
)


def _artifact(
    *,
    states: tuple[ArtifactState, ...] | None = None,
    transitions: tuple[ArtifactTransition, ...] | None = None,
    scenarios: tuple[ArtifactScenario, ...] | None = None,
    cases: tuple[ArtifactCase, ...] | None = None,
) -> Artifact:
    """拼一份默认合法的产物，按需覆盖某一段。"""
    return Artifact(
        states=states
        if states is not None
        else (
            ArtifactState("S1", "详情页", True, "截图：顶栏显示型号", "打开 App 后进入设备详情页"),
            ArtifactState("S2", "场景页", True, "截图：功能格场景高亮", "点击场景模式后进入场景页"),
        ),
        transitions=transitions
        if transitions is not None
        else (
            ArtifactTransition(
                "T1", "S1", "S2", "点击场景模式", "", "", "点击场景模式后进入场景页"
            ),
        ),
        scenarios=scenarios
        if scenarios is not None
        else (
            ArtifactScenario(
                "SC-001", "进入场景页", ("S1", "S2"), ("T1",), "主流程", "点击场景模式后进入场景页"
            ),
        ),
        cases=cases
        if cases is not None
        else (
            ArtifactCase(
                "TC-001",
                "进入场景页",
                "SC-001",
                "S1",
                (ArtifactStep("点击场景模式", "S2", ""),),
                (),
                ("场景法",),
                "P1",
                "点击场景模式后进入场景页",
            ),
        ),
    )


def test_clean_artifact_passes() -> None:
    report = check_artifact_facts(_artifact(), REQUIREMENT)
    assert report.passed
    assert report.blocking == ()


def test_source_not_in_requirement_blocks_with_excerpt() -> None:
    bad = ArtifactScenario(
        "SC-001", "进入场景页", ("S1", "S2"), ("T1",), "主流程", "支持 16 万色灯效"
    )
    report = check_artifact_facts(_artifact(scenarios=(bad,)), REQUIREMENT)
    assert not report.passed
    assert report.blocking[0].code == "SOURCE_NOT_IN_REQUIREMENT"
    assert "SC-001" in report.blocking[0].where


def test_dangling_state_blocks() -> None:
    case = ArtifactCase(
        "TC-001",
        "进入场景页",
        "SC-001",
        "S9",
        (ArtifactStep("点击场景模式", "S2", ""),),
        (),
        ("场景法",),
        "P1",
        "点击场景模式后进入场景页",
    )
    report = check_artifact_facts(_artifact(cases=(case,)), REQUIREMENT)
    assert any(item.code == "CASE_DANGLING_STATE" for item in report.blocking)


def test_dangling_scenario_blocks() -> None:
    case = ArtifactCase(
        "TC-001",
        "进入场景页",
        "SC-999",
        "S1",
        (ArtifactStep("点击场景模式", "S2", ""),),
        (),
        ("场景法",),
        "P1",
        "点击场景模式后进入场景页",
    )
    report = check_artifact_facts(_artifact(cases=(case,)), REQUIREMENT)
    assert any(item.code == "CASE_DANGLING_SCENARIO" for item in report.blocking)


def test_unlisted_number_blocks() -> None:
    case = ArtifactCase(
        "TC-001",
        "进入场景页",
        "SC-001",
        "S1",
        (ArtifactStep("3 秒内点击场景模式", "S2", ""),),
        (),
        ("场景法",),
        "P1",
        "点击场景模式后进入场景页",
    )
    report = check_artifact_facts(_artifact(cases=(case,)), REQUIREMENT)
    assert any(item.code == "CASE_NUMBER_UNTRACEABLE" for item in report.blocking)


def test_boundary_values_allow_their_own_numbers() -> None:
    case = ArtifactCase(
        "TC-001",
        "名称边界",
        "SC-001",
        "S1",
        (ArtifactStep("输入 23 个字符的名称", "S2", ""),),
        (ArtifactBoundary("名称长度", ("22", "23"), "名称最多 22 个字符"),),
        ("场景法", "边界值"),
        "P1",
        "点击场景模式后进入场景页",
    )
    report = check_artifact_facts(_artifact(cases=(case,)), REQUIREMENT)
    assert report.passed is True


def test_boundary_without_anchor_blocks() -> None:
    case = ArtifactCase(
        "TC-001",
        "名称边界",
        "SC-001",
        "S1",
        (ArtifactStep("输入名称", "S2", ""),),
        (ArtifactBoundary("名称长度", ("30", "31"), "名称最多 22 个字符"),),
        ("场景法",),
        "P1",
        "点击场景模式后进入场景页",
    )
    report = check_artifact_facts(_artifact(cases=(case,)), REQUIREMENT)
    assert any(item.code == "BOUNDARY_SOURCE_MISSING" for item in report.blocking)


def test_uncovered_transition_only_warns() -> None:
    extra = ArtifactTransition("T2", "S2", "S1", "返回", "", "", "点击场景模式后进入场景页")
    report = check_artifact_facts(
        _artifact(
            transitions=(
                ArtifactTransition(
                    "T1", "S1", "S2", "点击场景模式", "", "", "点击场景模式后进入场景页"
                ),
                extra,
            )
        ),
        REQUIREMENT,
    )
    assert report.passed is True
    assert any(item.code == "TRANSITION_NOT_COVERED" for item in report.warnings)


def test_observable_state_without_observe_by_blocks() -> None:
    states = (
        ArtifactState("S1", "详情页", True, "", "打开 App 后进入设备详情页"),
        ArtifactState("S2", "场景页", True, "截图：功能格场景高亮", "点击场景模式后进入场景页"),
    )
    report = check_artifact_facts(_artifact(states=states), REQUIREMENT)
    assert any(item.code == "STATE_OBSERVE_BY_MISSING" for item in report.blocking)


def test_format_facts_is_readable() -> None:
    text = format_facts(check_artifact_facts(_artifact(), REQUIREMENT))
    assert "确定性问题：0 条" in text
    assert "告警：" in text
