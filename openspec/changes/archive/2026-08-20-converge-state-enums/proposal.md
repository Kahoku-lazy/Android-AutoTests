## Why

执行侧状态枚举存在双真相源与口径漂移：`TestRunStatus` 双定义（`constants.py` 大写 PASSED 版 0 消费 vs `test_models.py` 小写版实际消费）、同一完成态在 DB/代码/前端有 4 种写法（`COMPLETED`/`completed`/`PASSED`/`SUCCESS`）、`TaskCard.outcome` 语义硬编码散落 12 处。这是 L1b 详档 §三审计的结论，也是后续引擎层/协议层引用 `models/` 类型的前置（枚举不定，下游返工）。

## What Changes

- **合并 TestRunStatus**：唯一真相源收敛到 `models/test_models.py`（5 值小写：pending/running/completed/stopped/failed），删除 `models/constants.py` 重复版
- **新增 TaskOutcome / TaskCardStatus 枚举**（`models/test_models.py`），含 `terminal_values()` / `fail_values()` 复用方法
- **执行链路引用枚举**：`state_machine.py`（流转表/dequeue/complete/fail/repair/recover）、`views/execution_steps.py`、`views/helpers.py`、`views/ai_execution.py`、`views/execution.py`、`recovery_helpers.py` 的硬编码字符串全部改引枚举
- **写库口径统一小写**：`complete()` 由 `"COMPLETED"` 改为 `TestRunStatus.COMPLETED.value`（`"completed"`）——**破坏性变更（BREAKING）**，DB 存量数据由数据迁移回填
- **数据迁移**：`tr_test_runs.status` 大写存量（COMPLETED/RUNNING/FAILED/STOPPED/PENDING）→ 小写回填
- **模型 choices 引枚举**：`TaskCard.status/outcome` choices 改 `TaskCardStatus`/`TaskOutcome`（Django 6 原生枚举支持，生成 AlterField 迁移）
- **constants.py 清理**：删除 `TestRunStatus`/`TestResult`/`QueueStatus` 三个无消费者枚举；`DeviceStatus` 收敛两态（删 OFFLINE/DISCONNECTED 幽灵值）
- **死代码删除**：`executors/ui/connect.py:55` 的 `OFFLINE/DISCONNECTED` 幽灵状态检查分支
- **基线断言更新**（显式）：`test_state_machine_baseline.py` 的"大写 COMPLETED"与"双枚举"锚定断言按新口径改写

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L1b-领域模型与枚举真相源.md`（§4.1-4.5 收敛设计、§6.1-6.4 迁移映射、§7 验收标准）
- ARCH：`dev_docs/03-设计与架构/设计-目标架构-设备交互协议与引擎分层.md`（§六 6.1 状态真相源收敛）
- 基线：OpenSpec 已归档 change `2026-08-20-refactor-baseline-tests`（本变更将显式更新其锚定断言）
- 无 PRD 变更（纯收敛/修复，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯收敛/修复类变更（统一状态值口径、消除双真相源），无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。写库口径变化属 bugfix（大小写不一致），不是新需求。

## Impact

- `models/test_models.py`（枚举合并与新增）、`models/constants.py`（删 3 枚举、DeviceStatus 两态）
- `apps/test_runner/`：models.py（choices）、state_machine.py、views/{execution_steps,helpers,ai_execution,execution}.py、recovery_helpers.py、executors/ui/connect.py、新增 migrations（AlterField + 数据回填）
- `apps/ai_assistant/views_drf.py:642`（统计映射补小写口径，视代码确认）
- 测试：`tests/test_runner/test_state_machine_baseline.py` 断言更新
- 前端零改动（`STATUS_LABEL_MAP` 已兼容大小写；L4 收敛属 Step 6）
