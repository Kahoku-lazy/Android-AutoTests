## Why

平台小助手「新建任务」弹窗没有独立标题、附件只是路径字符串且不进规划模型；任务卡片也不展示状态/时间/设备。用户现在需要把标题、目标、Word/PDF 解析后的 Markdown 与设备 ID 作为规划入参，并在同设备串行、异设备并行下发，否则多任务会抢同一台设备。

## What Changes

- 新建任务弹窗增加**任务标题**（必填）；**任务目标**仍必填；设备仍可选（留空则提交时解析为当时第一台在线设备并**落库**）。弹窗打开时立即拉设备列表，打开期间每 30 秒再拉 `GET /devices`，与设备管理心跳对齐。
- **BREAKING** 附件从「路径/URL 文本框」改为上传 **Word（.docx）或 PDF**（每任务至多一份）；服务端解析为 Markdown 后落库，原路径字符串不再作为规划输入。
- 任务卡片不再把目标当正文：展示**任务标题、状态、创建时间、设备名称**（有型号则型号，否则 serial）。
- 规划模型的用户输入改为固定 JSON 文本（字段名中文）：`任务标题` / `任务目标` / `附件文本内容` / `设备ID`。无附件时 `附件文本内容` 为空字符串。
- **后台调度（用户确认方案 1）**：每次提交仍只创建一条任务；同 `device_serial` 若已有 `running` 则新任务保持 `pending` 排队（FIFO）；不同 serial 可并行。任务终态后拉起同设备下一条 pending。
- 不改执行/验收模型工具集；不引入批量建任务弹窗；不新增 `cancelled`/`paused` 状态。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-需求总纲.md`（平台小助手任务发布；无独立「任务附件规划入参」PRD，本单以工作台弹窗需求为准）
- ARCH：`dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md`（AI 助手任务 → 引擎协议；设备互斥经 `device_pool`）
- 既有 OpenSpec：`openspec/specs/ai-task-publishing/spec.md`、`openspec/specs/ai-engine-protocol/spec.md`（主规格仍写旧「双线路/清单」字段，本单用 delta 覆盖当前实现）
- UI：Doodle Craft 弹窗/便签卡片规格（`.agents/skills/doodle-craft`）；前端模块 `frontend/src/modules/ai-assistant/`

## Capabilities

### New Capabilities

- `ai-task-device-dispatch`: 按已解析 `device_serial` 调度 AI 任务：同设备 FIFO 排队，异设备并行；进程重启后对遗留 `running` 失败处理并尝试拉起 pending。

### Modified Capabilities

- `ai-task-publishing`: 提交字段增加独立 title；附件改为文件上传并解析为 Markdown；列表卡片展示标题/状态/时间/设备名，不再以目标为卡片正文。
- `ai-engine-protocol`: Django 组装给规划阶段的用户输入 MUST 为上述四字段 JSON 字符串（仍经 `TaskRequest.goal` 传入引擎，避免为中文键另扩协议字段）。

## Impact

- 后端：`apps/ai_assistant`（`models.AITask.attachment` 扩为可存 Markdown 的 TextField、submit serializer/view、`create_task`、列表序列化补设备名、调度器、`finalize_task` 后入队、Word/PDF 解析复用 `kb_files`/`views_upload_drf` 已有解析）；`models.constants.TaskStatus` 仍四态，排队用 `pending`。
- 引擎：`engines/ai/agentscope` 规划仍吃 `req.goal` 字符串；`PLANNER_PROMPT` 补充「输入可能是任务 JSON」；不改 `TaskRequest` 字段集。
- 前端：`TaskBoard.vue` / `useTaskPublish.ts` / `api/tasks.ts` / `shared/types/ai.ts`；卡片与弹窗走既有 Doodle 组件。
- 测试：提交契约、解析失败拒绝、规划 JSON 组装、同 serial 排队/异 serial 并行、空设备无在线 fail-fast。
- HTTP 仍走 `frontend` 模块 `api.ts` → `/api`；写库只经 `apps/ai_assistant/api.py`。
