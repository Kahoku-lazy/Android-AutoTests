## Why

BUG 单现在只复制任务失败摘要，看不出工作流哪一步出错、期望是什么、实际差在哪。任务详情页已经下线，从 BUG 单也回不到步骤证据。

## What Changes

- **BREAKING**：当前工作流一次失败只登记一张 BUG 单，不再按 `result.failed` 里的步骤名拆成多张。标题用第一个失败步骤。
- 任务收口时把失败步骤写成结构化快照：序号、步骤名、期望结果、实际结果、尝试次数、原因类别。抛错和中断也写成同形的一步。BUG 单只保存并展示这张快照，不回读任务或报告。
- BUG 单详情按四问展示：出错步骤、原因类别、期望结果、实际结果。没有结构化快照的旧单仍显示原文。
- 有 HTML 报告时，详情提供「查看报告」；没有报告时只显示任务编号，不再链到已下线的 `/tasks/:id`。
- 历史按用例拆开的 BUG 单不迁移、不覆盖。重复同步不新建，也不覆盖人工处理状态。

## 关联文档

无独立需求编号。本次范围来自本轮确认：BUG 单要能回答工作流哪一步出错、原因、期望结果与实际结果。`PRD-平台总需求.md` 未单列 BUG 单字段，本变更只改台账与详情，不改任务状态口径。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`: 工作流失败改为一张单，详情展示失败步骤四问，报告入口替换已下线的任务详情链接。

## Impact

- 后端：`backend/apps/task_list/task_runner.py`、`backend/apps/bug_manager/`（模型、提取、序列化、迁移）。
- 前端：`frontend/src/modules/bug-manager/` 详情抽屉与任务/报告入口。
- 接口：`GET /api/bugs/` 与 `GET /api/bugs/{id}/` 增加失败步骤字段；任务列表摘要口径不变。
- 测试：`tests/bug_ticket/`、`tests/task/unit/test_task_closeout.py`、`frontend/tests/bug-manager/`。
