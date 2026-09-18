## Why

Step 5 已由后端下发权威 `state` 字段（running/queued/done/idle）。前端 `taskUtils.deriveTaskStatus` 仍用 status×outcome×running 三元组 if-else 重新推导（含同一漂移补丁），属双真相源残留；且 Step 1 收敛小写后，report-generator 的状态筛选键仍是旧大写（`COMPLETED/FAILED/STOPPED`），导致筛选/徽章失效。Step 6 收官：前端删推导、消费权威字段、统一小写口径。

## What Changes

- `test-runner/composables/taskUtils.ts`：`deriveTaskStatus`/`isTaskQueued`/`taskBucket` 改读权威 `task.state`（无 state 的本地/旧数据回退 `idle`，属字段读取非推导）；判定分支（含漂移补丁）删除；`running` 字段保留为本地镜像（与 state 同步写入），既有 `task.running` 读取点不受影响
- 本地状态变更点补 state 同步：`index.vue`（启动/排队/失败/取消/停止/队列激活/新任务创建×2）、`useTaskOperations.ts`、`useTaskWebSocket.ts`（run_finished/device_error）、`TaskDetail.vue`（停止/激活/取消/重建）
- `loadTasks` 映射加 `state: d.state || ""`
- `report-generator` 大小写收敛：`api.ts` STATUS_LABEL_MAP/statusBadgeClass、`constants.ts` STATUS_KEYS/LABELS/徽章映射、`index.vue` 筛选 tabs、`TaskReport.vue` 状态映射 → 全小写键
- 范围外登记：ai-assistant `ChatView.vue:104-115`/`HintCard.vue:15-19` 的大写状态显示属 AI 任务域，非 tr_test_runs，不在本序列（另行评估）

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L4-前端模块职责与边界.md`（§六 收敛项 4/5）
- 基线：OpenSpec 已归档 `2026-08-20-backend-authoritative-task-state`
- 无 PRD 变更（判定收敛 + 口径统一，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 判定收敛 + 口径统一（展示语义不变）：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 修改：`frontend/src/modules/test-runner/{composables/taskUtils.ts,index.vue,composables/useTaskOperations.ts,composables/useTaskWebSocket.ts,components/TaskDetail.vue}`、`frontend/src/modules/report-generator/{api.ts,constants.ts,index.vue,TaskReport.vue}`
- 后端零改动；数据库零改动
