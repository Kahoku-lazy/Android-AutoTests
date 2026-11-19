## Why

AI 助手工作流现在按任务立即启动，不看手机，所以同一台手机可以同时跑两条任务。任务清单仍用卡片展示全部任务，并保留自己的新建入口，和「只记录工作流任务」的定位不一致。

## What Changes

- 工作流任务并入现有设备槽：同一可连接地址按任务编号排队，不同地址并行。
- **BREAKING**：工作流提交必须选择设备。空设备不再创建任务。
- **BREAKING**：任务清单不再提供新建任务入口，也不再展示设备执行或用例编写记录。
- 任务清单改为设备管理同款表格：工作流分类与执行状态分开筛选，表格实线、无阴影、固定行高。
- 删除排队任务后补一次同机派发。停机排空拒绝派发时记录日志，不改变停机规则。

## 关联文档

无独立需求编号。本次范围来自本轮确认：工作流同机排队、空设备拒绝、任务清单只展示工作流记录，并以设备管理表格为样式基准。`PRD-平台总需求.md` 仍描述任务清单自己新建任务，本变更会改掉该入口。

## Capabilities

### New Capabilities

- `workflow-device-queue`：工作流任务按可连接地址排队，空设备拒绝，删除排队任务后补派发。

### Modified Capabilities

- `assistant-bound-sop`：设备从可空改为必选，运行弹窗去掉「不指定设备」。
- `ai-task-list`：任务清单只展示工作流记录，去掉新建入口和卡片分组，改为表格与双筛选。
- `task-card-sop-form`：退役任务清单自己的新建任务弹窗。
- `ai-task-publishing`：任务清单不再承担设备执行与用例编写的新建入口。
- `task-list-module`：任务清单路由只保留列表页，不再要求迁入新建弹窗。

## Impact

- 后端：`backend/apps/task_list/api.py`、`views.py`、`task_runner.py`。
- 前端：`frontend/src/modules/task-list/`、`frontend/src/modules/ai-assistant/components/SopRunForm.vue`。
- 测试：`tests/task/unit/test_assistant_sop.py`、设备调度单测、`frontend/tests/task-list/`、`frontend/tests/ai-assistant/`。
- 不改仪表盘 `agent` 字段错误，不改重跑函数的旧签名，不改 SOP 步骤重试与失败汇总。
