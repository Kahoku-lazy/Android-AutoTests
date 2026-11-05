"""产物渲染：Markdown 三节固定顺序，Mermaid 由产物派生。"""

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
from engines.agents.workflow.case_artifact_render import (
    render,
    render_markdown,
    render_mermaid,
)


def _artifact(**overrides) -> Artifact:
    """默认一份含两状态、一条迁移、一条场景、一条用例的产物。"""
    defaults = {
        "states": (
            ArtifactState("S1", "详情页", True, "截图：顶栏显示型号", "打开 App 后进入设备详情页"),
            ArtifactState("S2", "场景页", True, "截图：功能格场景高亮", "点击场景模式后进入场景页"),
        ),
        "transitions": (
            ArtifactTransition(
                "T1", "S1", "S2", "点击场景模式", "设备已连接", "", "点击场景模式后进入场景页"
            ),
        ),
        "scenarios": (
            ArtifactScenario(
                "SC-001", "进入场景页", ("S1", "S2"), ("T1",), "主流程", "点击场景模式后进入场景页"
            ),
        ),
        "cases": (
            ArtifactCase(
                "TC-001",
                "点击场景模式",
                "SC-001",
                "S1",
                (ArtifactStep("点击场景模式", "S2", ""),),
                (ArtifactBoundary("名称长度", ("22", "23"), "名称最多 22 个字符"),),
                ("场景法", "边界值"),
                "P1",
                "点击场景模式后进入场景页",
            ),
        ),
    }
    defaults.update(overrides)
    return Artifact(**defaults)


def test_markdown_has_three_sections_in_order() -> None:
    text = render_markdown(_artifact())
    first = text.index("## 一、需求状态机")
    second = text.index("## 二、业务流场景")
    third = text.index("## 三、测试用例")
    assert first < second < third


def test_markdown_counts_line() -> None:
    text = render_markdown(_artifact())
    assert "状态 2 个、迁移 1 条、场景 1 条、用例 1 条" in text


def test_case_table_renders_steps_and_boundary() -> None:
    text = render_markdown(_artifact())
    assert "1) 点击场景模式 → S2" in text
    assert "名称长度：22/23" in text
    assert "场景法、边界值" in text


def test_empty_artifact_has_readable_placeholders() -> None:
    text = render_markdown(Artifact())
    assert text.count("（尚未产出") == 3


def test_mermaid_lists_every_transition() -> None:
    diagram = render_mermaid(_artifact())
    assert diagram.startswith("stateDiagram-v2")
    assert 'state "详情页" as S1' in diagram
    assert "S1 --> S2 : 点击场景模式 [设备已连接]" in diagram


def test_mermaid_escapes_quotes() -> None:
    states = (ArtifactState('S"1', '详情"页', True, "截图", "打开 App 后进入设备详情页"),)
    diagram = render_mermaid(_artifact(states=states))
    assert "详情'页" in diagram
    assert diagram.count('"') == 2


def test_mermaid_empty_without_states() -> None:
    assert render_mermaid(Artifact()) == ""


def test_render_is_derived_from_artifact() -> None:
    before_doc, before_diagram = render(_artifact())
    extra = ArtifactState("S3", "灯效页", True, "截图", "点击灯效进入灯效页")
    after_doc, after_diagram = render(_artifact(states=(*_artifact().states, extra)))
    assert before_doc != after_doc
    assert before_diagram != after_diagram
    assert "S3" in after_diagram


def test_uncertain_marks_are_visible() -> None:
    state = ArtifactState("S1", "详情页", False, "仅内部计数", "打开 App 后进入设备详情页", True)
    text = render_markdown(_artifact(states=(state,)))
    assert "（待确认）" in text
    assert "（不可观察）" in render_mermaid(_artifact(states=(state,)))
