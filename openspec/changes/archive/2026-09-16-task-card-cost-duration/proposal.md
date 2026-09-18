## Why

任务看板卡片目前只展示状态、创建时间、设备、助手，执行中/已完成任务的 DeepSeek 费用与耗时只能进详情才看得到，列表上无法区分成本和时长。需要在卡片 meta 中直接展示这两项。

## What Changes

- 任务列表行 DTO 增加 `deepseek_cost`、`started_at`、`finished_at`（与详情同一计价与时间字段，不新增表列）。
- 任务卡片 meta 增加「费用」「耗时」两行；未开始或未结束时耗时为「—」，费用按既有 `task_deepseek_cost` 显示（无用量为 0.0000 元）。
- 不改调度、不改详情页 KPI、不改仪表盘聚合。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-需求总纲.md`（平台小助手任务发布看板）
- ARCH：`dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md`（ai_assistant 任务发布）
- 计价：`apps/ai_assistant/deepseek_billing.py`（与详情页共用）

## Capabilities

### New Capabilities

- `ai-assistant/task-card-cost-duration`: 任务列表卡片展示 AI 费用与执行耗时；列表 API 行数据提供费用与起止时间。

### Modified Capabilities

- （无；仓库尚无主 spec）

## Impact

- `apps/ai_assistant/api.py`：`serialize_agent_task_row`
- `frontend/src/shared/types/ai.ts`：`TaskRecord`
- `frontend/src/modules/ai-assistant/components/TaskBoard.vue`：卡片 meta
- 单测：`tests/graybox/unit/test_ai_task_title_attach_dispatch.py`（行序列化）；必要时补前端卡片字段断言
