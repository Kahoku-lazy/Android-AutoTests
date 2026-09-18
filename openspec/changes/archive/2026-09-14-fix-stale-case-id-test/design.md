## Context

动机见 `proposal.md` - Why。这是**测试未跟上模型重构**的典型：`CaseFile` 表格页重构把「用例行必须挂文件」变成硬约束，生产代码与 API 都带了 `file_id`，只有这个单测还在构造「无文件的用例行」。

## Goals / Non-Goals

**Goals:**

- 让该用例反映当前数据模型（用例行挂在 `CaseFile` 下）
- 恢复 `next_case_id` 同日递增的行为覆盖

**Non-Goals:**

- 不放松模型（不给 `file` 加回 `null=True`）—— 那是重构后的有意约束
- 不改 `next_case_id()` 逻辑（它只按 ID 前缀取最大号，与 `file` 无关）
- 不批量排查其它 App 的过期测试（本单只修已实测失败的那条）

## Decisions

### 1. 补 `file`，而不是删掉该用例

- **选择**：加一个最小 `CaseFile`（`project` + `name`）并传 `file=`
- **理由**：`next_case_id` 的「同日递增」是唯一覆盖该行为的用例；删掉等于丢掉覆盖。`CaseFile` 的必填字段只有 `project` / `name`（`directory` 可空、`sort_order` 有默认）

### 2. 顺带补 import，保持模块顶部导入风格

- **选择**：`from apps.case_manager.models import CaseFile`（与既有两行模型 import 并列）
- **理由**：文件既有风格是每个模型一行 import（`CaseProject` / `TestDefinition as CaseDoc`）

## 模块防火墙自检

- 跨模块写库：不涉及（测试内建对象，且同 App）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [测试变成「只测不炸」] → 断言不变（仍断言 `next_case_id() == f"TC-{today}-0004"`），只补足构造数据

## Migration Plan

1. 给用例补 `CaseFile` 与 `file=`
2. 跑 `pytest tests/graybox/unit/test_case_manager_ids.py -q` 与 `pytest tests/graybox/unit -q`
3. 归档；回滚 = `git checkout` 该测试文件
