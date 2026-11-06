## Why

AI 助手页要 5 秒、任务清单页也要 5 秒：两个页面都在搬同一份 13MB 的智能体列表。库里 `ai_agents.avatar` 和 `route_configs.device_control.avatar` 各存了一份 6.5MB 的 base64，前端却早已改用静态 `agent-avatar.svg`；任务清单还用 `select_related("agent")` 联表，把这两块大字段随每条任务再取一遍。

## What Changes

- **接口不再下发头像大字段**：`GET /api/ai/agents/` 与 `GET /api/ai/agents/{id}/` 去掉 `avatar` 与 `route_configs.*.avatar`（前端所有渲染已用静态图标）。
- **历史数据清理**：一次性把 `ai_agents.avatar` 与 `route_configs.*.avatar` 中超长（>4KB）的值清空，并给写入加长度上限，避免再塞回 6.5MB。
- **任务列表不再联表取大字段**：任务行只取自身列；线路名用一次 `JSON_EXTRACT` 从 `route_configs->device_control->name` 取，不把整个 route_configs 读进内存；附件改为 `prefetch_related` 批量取。
- **任务清单轮询加在途守卫**：请求未返回时跳过本轮，间隔 5s → 10s。
- 不改页面视觉、不改任务/智能体字段语义、不改统计口径。

## 关联文档

- PRD：`PRD-平台总需求` 一、1.4 产品边界（AI 助手 / 任务清单为平台主入口）——本变更只修加载体积与查询方式。
- 既有规格：`openspec/specs/ai-assistant`（智能体接口契约）、`openspec/specs/task-list-module`（任务清单接口与轮询）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-assistant`: 新增「列表与详情不下发头像大字段」要求。
- `task-list-module`: 新增「任务列表查询预算与轮询不叠加」要求。

## Impact

- 后端：`backend/apps/ai_assistant/serializers.py`、`backend/apps/task_list/views.py`、`backend/apps/task_list/api.py`、新数据迁移。
- 前端：`frontend/src/modules/task-list/composables/useTaskList.ts`、`frontend/src/shared/types/ai.ts`（avatar 可选）。
- 接口：两处响应体从 13.1MB 降到 1KB 级；`/api/tasks/` 的 SQL 从 22 条降到 3 条以内、单条 1.4s 的联表消失。
- OpenAPI 基线随接口字段变化更新。
- 非目标：头像上传能力（当前 UI 已固定内置图标）；任务详情报告；仪表盘。
