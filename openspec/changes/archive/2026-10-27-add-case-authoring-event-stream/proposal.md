# 用例编写报告展示模型事件流

## Why

用例编写报告目前只有最终用例文档与判决，无法回看模型如何拆需求、调用工具、被验收驳回。出问题时分不清是需求理解、方法选择还是提示词纪律的问题，只能翻日志文件。

## What Changes

- `GET /api/tasks/{id}/report/` 对 `case_authoring` 任务增加 `events` 时间线：按 seq 升序返回事件类型、标签、时间、角色、模型、状态与详情。
- 角色映射补齐：`case_writer_role` → `case_writer`，`case_verifier_role` → `verifier`，前端按角色着色。
- 事件详情单条截断到 4000 字，完整交付文档仍只放 `document`，避免重复传输。
- 任务详情页在「生成的测试用例」之后增加「模型事件流」区块，长文本框内滚动查看。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `appliance-case-authoring-task`：用例编写报告增加模型事件流，供人工复核编写过程。

## Impact

- 后端：`backend/apps/task_list/task_reports.py`。
- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue` 与其样式。
- 测试：`tests/api/test_task_case_authoring.py`。
- 不影响设备执行任务的报告结构；设备任务不返回 `events`。
