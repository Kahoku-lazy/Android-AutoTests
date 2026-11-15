"""三段式产物契约与存储：结构校验、批次原子性、计数读取。"""

from __future__ import annotations

import pytest

from engines.agents.workflow.case_artifact import (
    MAX_BATCH,
    ArtifactCase,
    ArtifactError,
    ArtifactScenario,
    ArtifactState,
    ArtifactStore,
)


def _state(**overrides) -> dict:
    payload = {
        "id": "S1",
        "name": "详情页",
        "observable": True,
        "observe_by": "截图：顶栏显示型号",
        "source": "打开 App 后进入设备详情页",
    }
    payload.update(overrides)
    return payload


def _transition(**overrides) -> dict:
    payload = {
        "id": "T1",
        "from": "S1",
        "to": "S2",
        "event": "点击场景模式",
        "source": "点击场景模式后进入场景页",
    }
    payload.update(overrides)
    return payload


def _scenario(**overrides) -> dict:
    payload = {
        "id": "SC-001",
        "title": "进入场景页",
        "path": ["S1", "S2"],
        "transitions": ["T1"],
        "type": "主流程",
        "source": "点击场景模式后进入场景页",
    }
    payload.update(overrides)
    return payload


def _case(**overrides) -> dict:
    payload = {
        "id": "TC-001",
        "title": "进入场景页",
        "scenario_id": "SC-001",
        "pre_state": "S1",
        "steps": [{"action": "点击场景模式", "expect_state": "S2"}],
        "boundary": [],
        "method": ["场景法"],
        "priority": "P1",
        "source": "点击场景模式后进入场景页",
    }
    payload.update(overrides)
    return payload


def _seeded_store() -> ArtifactStore:
    store = ArtifactStore()
    store.put_state_machine(
        [_state(), _state(id="S2", name="场景页", source="进入场景页")],
        [_transition()],
    )
    store.append_scenarios([_scenario()])
    return store


def test_state_requires_source() -> None:
    with pytest.raises(ArtifactError, match="source 不能为空"):
        ArtifactState.parse(_state(source=" "), "第 1 条状态")


def test_state_observable_must_be_bool() -> None:
    with pytest.raises(ArtifactError, match="observable 必须是布尔值"):
        ArtifactState.parse(_state(observable="是"), "第 1 条状态")


def test_transition_unknown_state_rejected() -> None:
    store = ArtifactStore()
    with pytest.raises(ArtifactError, match="指向未声明的状态"):
        store.put_state_machine([_state()], [_transition(to="S9")])


def test_scenario_path_too_short_rejected() -> None:
    with pytest.raises(ArtifactError, match="至少要有两个状态"):
        ArtifactScenario.parse(_scenario(path=["S1"]), "第 1 条场景")


def test_scenario_type_limited() -> None:
    with pytest.raises(ArtifactError, match="type 必须是"):
        ArtifactScenario.parse(_scenario(type="随便"), "第 1 条场景")


def test_batch_limit_enforced() -> None:
    store = ArtifactStore()
    too_many = [_scenario(id=f"SC-{index:03d}") for index in range(MAX_BATCH + 1)]
    with pytest.raises(ArtifactError, match=f"一次最多 {MAX_BATCH} 条"):
        store.append_scenarios(too_many)


def test_same_id_overwrites_in_place() -> None:
    """同 id 再写一次是原位覆盖，不新增条数（驳回后定点改的场景）。"""
    store = _seeded_store()
    store.append_scenarios([_scenario(title="进入场景页（修订）")])
    assert store.counts()["scenarios"] == 1
    assert store.scenarios[0].title == "进入场景页（修订）"


def test_scenario_unknown_transition_rejected() -> None:
    store = ArtifactStore()
    store.put_state_machine(
        [_state(), _state(id="S2", name="场景页", source="进入场景页")],
        [_transition()],
    )
    with pytest.raises(ArtifactError, match="未声明的迁移"):
        store.append_scenarios([_scenario(transitions=["T9"])])


def test_case_requires_steps() -> None:
    with pytest.raises(ArtifactError, match="steps 不能为空"):
        ArtifactCase.parse(_case(steps=[]), "第 1 条用例")


def test_case_requires_scenario_method() -> None:
    with pytest.raises(ArtifactError, match="method 必须含「场景法」"):
        ArtifactCase.parse(_case(method=["边界值"]), "第 1 条用例")


def test_case_unknown_state_rejected() -> None:
    store = _seeded_store()
    with pytest.raises(ArtifactError, match="引用了未声明的状态"):
        store.append_cases([_case(steps=[{"action": "点击", "expect_state": "S9"}])])


def test_append_cases_accumulates() -> None:
    store = _seeded_store()
    for index in range(1, 4):
        store.append_cases([_case(id=f"TC-{index:03d}", title=f"用例 {index}")])
    assert store.counts()["cases"] == 3


def test_invalid_batch_is_atomic() -> None:
    store = _seeded_store()
    bad_batch = [_case(id="TC-001"), _case(id="TC-002", scenario_id="SC-999")]
    with pytest.raises(ArtifactError, match="scenario_id 未声明"):
        store.append_cases(bad_batch)
    assert store.counts()["cases"] == 0


def test_read_counts_only_by_default() -> None:
    store = _seeded_store()
    assert store.read() == "状态 2 条、迁移 1 条、场景 1 条、用例 0 条"


def test_read_section_returns_payload() -> None:
    store = _seeded_store()
    text = store.read("scenarios", counts_only=False)
    assert "SC-001" in text
    assert "点击场景模式后进入场景页" in text


def test_read_unknown_section_is_readable() -> None:
    store = _seeded_store()
    assert "未知分节" in store.read("bogus", counts_only=False)
