## Context

- 现状：`apps/dashboard/views.py` 中 `_daily_execution_series` / `_recent_tasks` 注释写明执行引擎已下线，恒返回零与 `[]`。前端 `TrendBarChart` 绑定 `charts.execution`，`TaskResultPanel` 绑定 `recent_tasks`，点击写死 `/reports`。
- 真相源：助手任务为 `AITask`（`ai_tasks`），列表已由 `GET /ai/agent-tasks` 与 `serialize_agent_task_row` 提供。仪表盘已只读 `AITask` 做用量统计（`ai_usage.py` 的 `_task_qs`）。
- 助手卡：`TaskBoard.vue` 的 `DoodleNote` 目前含 badge、goal、meta、result、删除。

## Goals / Non-Goals

**Goals:**

- 趋势第一行图表 + 结果面板改绑 `AITask`（与用量同一用户可见智能体口径）
- 结果行进入助手任务详情
- 助手列表卡收敛为标题 + 详情

**Non-Goals:**

- 不恢复 test_runner / 执行引擎
- 不改每日 Token / DeepSeek 费用图
- 不改任务详情页、提交/删除/清空 API
- 不把仪表盘前端 import `ai-assistant/api`（数据走既有 `/dashboard/stats/`）

## Decisions

### 1. 后端聚合，不让仪表盘前端直打任务列表

- **选择**：扩展 dashboard stats 的 `charts.execution` / `execution_summary` / `recent_tasks`。
- **理由**：仪表盘是全平台只读聚合区；前端已有映射，契约字段名可复用。
- **备选**：dashboard 模块再调 `/ai/agent-tasks` —— 双请求、口径易与用量过滤不一致。

### 2. 分日按 created_at，成功/失败按任务 status

- **选择**：12 日标签与现用量图同一套日期算法；`completed`/`success` → success 柱，`failed` → failed 柱；pending/running/cancelled/paused 不计柱但可出现在最近列表。
- **理由**：对齐现有双柱组件，改数据不改图类型。
- **备选**：第三柱「进行中」——超出用户点名的两块区域。

### 3. recent_tasks 形状尽量兼容 RecentTask

- **选择**：`id`、`title`、`status`（success/failed/running/idle 等面板已有 meta）、`time`；不填 `cases`。
- **理由**：少改面板模板；去掉用例点阵即可。

### 4. 助手卡保留分组与头栏

- **选择**：只砍卡片内容；分组 collapse 仍表达状态。
- **理由**：用户指定的是卡片，不是整段 Task 工具条。

## 模块防火墙自检

- 仪表盘继续只读 import `apps.ai_assistant.models.AITask` 与已有 `filter_agents_for_user`；无写操作。
- 前端 dashboard 不 import ai-assistant 内部模块。

## Risks / Trade-offs

- [柱图不含进行中] 当日全是 pending 时柱为 0，右侧列表仍有卡 → 文案/图例标明成功与失败。
- [status 映射] 列表 `completed` 与面板 `success` 需统一，避免图标落到 idle。

## Migration Plan

1. 改 dashboard 聚合函数。
2. 改 TrendBarChart 图例与 TaskResultPanel 跳转/空态。
3. 收敛 TaskBoard 卡片。
4. 回滚：还原三处文件即可。

## Open Questions

（无。图类型沿用现有双柱；卡片范围按用户 DOM 指定。）
