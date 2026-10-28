"""确定性校验：解析用例表、核对 ID/字段/方法数/比例，并回写第六节统计。"""

from __future__ import annotations

import pytest

from engines.agents.workflow.case_document_check import (
    case_step_pairs,
    check_and_fix_document,
    check_case_document,
    fix_case_statistics,
    parse_case_document,
)

pytestmark = [pytest.mark.unit]


def sample_document(
    *, trace: str = "REQ-001", method: str = "场景流+边界值", status: str = "NOT_RUN"
) -> str:
    return f"""## 一、需求原子表

| 原子ID | 来源章节 | 需求原子 | 类型 | 用户可感知 | 物理依赖 | 备注 |
|:--:|:--:|------|:--:|:--:|:--:|------|
| REQ-001 | 1 | 待机单击 POWER 开机 | 按键 | ✅ | 无 | |
| REQ-002 | 1 | 运行中单击 POWER 关机 | 按键 | ✅ | 无 | |

## 二、方法分配表（需求追溯矩阵）

| 原子ID | 复杂度 | 选用方法 | 用例编号 | 用例标题 | 备注 |
|:--:|:--:|------|:--:|------|------|
| REQ-001 | L1 | 场景流+边界值 | TC-H717D-BTN-V1-001 | 开机 | |
| REQ-002 | L1 | 场景流+边界值 | TC-H717D-BTN-V1-002 | 关机 | |

## 三、需求冲突登记表

| 冲突ID | 需求A | 需求B | 矛盾 | 用例处理 | 状态 |
|:--:|------|------|------|------|:--:|
| — | — | — | 未发现需求冲突 | — | — |

## 四、测试用例

### 4.1 按键

| 用例编号 | 测试标题 | 追溯ID | 方法 | 复杂度 | 优先级 | 前置条件 | 测试步骤 | 预期结果 | 量化指标 | 校验要点 | 状态 | 执行记录 |
|------|------|:--:|:--:|:--:|:--:|------|------|------|:--:|------|:--:|:--:|
| TC-H717D-BTN-V1-001 | 待机开机 | {trace} | {method} | L1 | P1 | 设备待机；环境常规；工具秒表；固件 V1 | 1) 单击 POWER | 模式灯亮且持续 1s | ≤1s | 看灯态 | {status} | {{}} |
| TC-H717D-BTN-V1-002 | 运行中关机 | REQ-002 | 场景流+边界值 | L1 | P1 | 设备运行；环境常规；工具秒表；固件 V1 | 1) 单击 POWER | 所有灯熄灭且持续 1s | ≤1s | 看灯态 | NOT_RUN | {{}} |

## 五、E2E 用户旅程

| E2E编号 | 用户旅程 | 涉及模块 | 关键验证点 |
|:--:|------|------|------|
| E2E-01 | 开机到关机 | BTN | 灯态 |
| E2E-02 | 关机到开机 | BTN | 灯态 |
| E2E-03 | 重复开关机 | BTN | 灯态 |

## 六、覆盖与门禁自检

| 指标 | 数值 | 结论 |
|------|:--:|------|
| 需求原子数 | 999 | 模型自检 |

## 七、待确认问题

| 编号 | 问题 | 影响原子/用例 | 需要谁确认 |
|:--:|------|------|------|
| 无 | 无 | 无 | 无 |
"""


def test_parse_case_document_reads_atoms_cases_and_e2e():
    parsed = parse_case_document(sample_document())

    assert list(parsed.atoms) == ["REQ-001", "REQ-002"]
    assert [case.case_id for case in parsed.cases] == [
        "TC-H717D-BTN-V1-001",
        "TC-H717D-BTN-V1-002",
    ]
    assert parsed.e2e_count == 3
    assert parsed.sections == set("一二三四五六七")


def test_fix_case_statistics_replaces_model_numbers():
    fixed = fix_case_statistics(sample_document())

    assert "| 需求原子数 | 2 |" in fixed
    assert "| 用例数 | 2 |" in fixed
    assert "| E2E 条数 | 3 |" in fixed
    assert "999" not in fixed


def test_check_case_document_accepts_complete_document():
    fixed, issues = check_and_fix_document(sample_document())

    assert issues == []
    assert "| 需求原子数 | 2 |" in fixed


def test_check_case_document_flags_orphan_trace_and_missing_method():
    issues = check_case_document(sample_document(trace="REQ-999"))

    assert any("REQ-999" in issue for issue in issues)


def test_check_case_document_flags_method_floor_and_status():
    issues = check_case_document(sample_document(method="场景流", status="UNTESTABLE"))

    assert any("低于 2" in issue for issue in issues)
    assert any("UNTESTABLE" in issue for issue in issues)


def test_check_case_document_flags_p0_ratio():
    document = sample_document().replace("| L1 | P1 |", "| L1 | P0 |")
    issues = check_case_document(document)

    assert any("超过 30%" in issue for issue in issues)


def test_parse_case_document_tracks_module_heading():
    document = sample_document().replace(
        "## 四、测试用例", "## 模块：按键（BTN）· 验收 PASS\n\n## 四、测试用例"
    )
    parsed = parse_case_document(document)

    assert [case.module for case in parsed.cases] == ["按键", "按键"]


def test_parse_case_document_falls_back_to_subsection():
    document = sample_document().replace("## 四、测试用例", "## 四、测试用例\n\n### 4.1 按键")
    parsed = parse_case_document(document)

    assert parsed.cases[0].module == "按键"


def test_case_step_pairs_splits_and_strips_numbers():
    parsed = parse_case_document(sample_document())
    case = parsed.cases[0]
    case.fields["测试步骤"] = "1) 上电<br>2) 单击 POWER<br>3) 等待 3s"
    case.fields["预期结果"] = "1) 灯亮<br>2) 听到提示音<br>3) 3s 后熄灭"

    assert case_step_pairs(case) == [
        ("上电", "灯亮"),
        ("单击 POWER", "听到提示音"),
        ("等待 3s", "3s 后熄灭"),
    ]


def test_case_step_pairs_falls_back_when_counts_differ():
    parsed = parse_case_document(sample_document())
    case = parsed.cases[0]
    case.fields["测试步骤"] = "1) 上电<br>2) 单击 POWER<br>3) 等待 3s"
    case.fields["预期结果"] = "1) 灯亮<br>2) 听到提示音"

    assert case_step_pairs(case) == [("上电；单击 POWER；等待 3s", "灯亮；听到提示音")]


def test_case_step_pairs_returns_empty_for_missing_side():
    parsed = parse_case_document(sample_document())
    case = parsed.cases[0]
    case.fields["预期结果"] = ""

    assert case_step_pairs(case) == []
