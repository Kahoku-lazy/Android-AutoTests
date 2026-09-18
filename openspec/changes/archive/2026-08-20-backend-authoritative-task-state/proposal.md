## Why

任务状态判定当前前后端双真相源：后端 `state_machine` 管 status/outcome/running 三字段流转，前端 `taskUtils.deriveTaskStatus/taskBucket` 用 if-else 再推导一遍（含"queued+终态 outcome"漂移补丁，与后端 `repair_queued_terminal_drift` 是同一 bug 的双份修复）。Step 5 落地"后端下发权威 state"：状态判定收敛到 `state_machine.display_state(tc)` 唯一入口，REST 列表下发 `state` 字段，前端（Step 6）删推导只留展示映射。同时关闭 Step 4 登记项：`settings.DEVICE_ENGINE` 接线。

## What Changes

- `apps/test_runner/state_machine.py`：新增 `display_state(tc) -> str`（唯一判定处）——`running/queued/done/idle` 四值，含 queued+终态漂移兼容（语义与 `repair_queued_terminal_drift` 一致）
- `apps/test_runner/views/task_views.py::task_card_list`：序列化加 `"state": sm.display_state(tc)`（status/outcome/running 原字段保留，向后兼容）
- `config/settings.py`：新增 `DEVICE_ENGINE = "airtest_u2"`；`apps/device_pool/session.py` 工厂改经 settings 取引擎名（关闭 Step 4 登记项）
- 基线断言显式更新：`test_state_machine_baseline.py` 序列化测试增 `state` 字段断言
- 新增 `display_state` 单元测试（5 分支 + 漂移用例）

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L1b-领域模型与枚举真相源.md`（§6 收敛映射）、`设计-目标架构-设备交互协议与引擎分层.md`（§六 6.1 权威状态下发）
- 基线：OpenSpec 已归档 `2026-08-20-converge-state-enums`、`2026-08-20-introduce-device-session`（本变更关闭其登记项）
- 无 PRD 变更（契约增量字段 + 判定收敛，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 判定收敛 + 增量字段（向后兼容，前端旧推导仍可用至 Step 6 切换）：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 修改：`apps/test_runner/state_machine.py`、`apps/test_runner/views/task_views.py`、`config/settings.py`、`apps/device_pool/session.py`、`tests/test_runner/test_state_machine_baseline.py`
- 前端零改动（Step 6 切换消费）；数据库零改动
