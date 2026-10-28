# 家电测试用例编写任务（Agent-02）

## Why

平台已有「设备执行」任务链，但用例编写只能停在引擎脚本里：AI 助手看不到 Agent-02，任务清单只认设备 SOP，测试报告里也没有生成结果。需要把「上传 PRD/Word → 解析 → 编写并验收用例 → 报告查看」做成一条可操作的任务链。

## What Changes

- `AIAgent` 增加 `task_kind`（`device_control` / `case_authoring`），迁移种子 Agent-02，职责为「测试用例编写」。
- AI 助手看板改为每个可见 Agent 一张卡；Agent-02 显示 `职责：测试用例编写` 与 `case_authoring_workflow`。
- `Task` 增加 `task_kind` 快照；任务清单改为当前用户可见 Agent 的全部任务（设备执行 + 用例编写）。
- 新建任务弹窗按所选 Agent 切换表单：Agent-02 只要求任务标题 + PRD/Word 文档（`.docx` / `.pdf` / `.md`），不要求设备与 YAML。
- 用例编写任务由后台线程调用 `CaseAuthoringWorkflow`（编写角色 + 验收角色，最多两次尝试），把全文文档与判决写入 `Task.result`。
- 测试报告列表增加「类型」列；任务详情报告返回 `document` / `documents` / `conclusion.verdicts`，前端渲染净化后的 Markdown 与验收意见。

## Capabilities

### New Capabilities

- `appliance-case-authoring-task`：Agent-02 的注册、文档上传任务、后台用例编写执行与报告展示。

### Modified Capabilities

无。

## Impact

- 后端：`ai_assistant`（`AIAgent.task_kind`、Agent-02 迁移、Agent 列表 DTO）、`task_list`（`Task.task_kind`、文档上传、调度、执行、报告）。
- 前端：`ai-assistant`（多 Agent 卡片、职责/工作流）、`task-list`（按类型切换新建表单、详情文档面板）、`report-generator`（类型列）。
- 数据库：新增迁移 `ai_assistant/0061`、`task_list/0004`；不改旧表结构语义，不删除旧数据。
- 不影响现有设备执行任务：未选择 Agent-02 时仍走 YAML + 设备 + 原 SOP。
