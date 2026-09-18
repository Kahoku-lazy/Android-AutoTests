## Why

AI 助手的 token 用量、对话次数、缓存命中目前**无法统计**：`ai_messages` 虽有 `tokens`/`input_tokens` 字段但实测恒为 0（后端持久化未捕获 `MODEL_CALL_END` 的用量），缓存命中更无字段、无落库。仪表盘（纯只读聚合层）因此缺少 AI 用量可视性，用户无法了解模型成本与缓存收益。

## What Changes

1. **AI 用量落库（`apps/ai_assistant`）**：
   - `ai_messages` 新增 `cache_input_tokens`、`cache_creation_input_tokens` 字段（缓存命中/写入 token），迁移落库。
   - 后端 `_agent_stream` 捕获 `MODEL_CALL_END` 的 `input_tokens`/`output_tokens` 并随 `save_message` 持久化（`tokens`=输出、`input_tokens`=输入、`model_name`=模型名）。
   - 缓存命中经 AgentScope `on_model_call` 中间件捕获 `ChatUsage.cache_input_tokens`/`cache_creation_input_tokens`，随本轮回复落库。
2. **仪表盘聚合（`apps/dashboard`）**：`GET /api/dashboard/stats/` 新增 `ai_usage` 字段，只读聚合 `ai_conversations` + `ai_messages`：对话总数、输入/输出 token、缓存命中 token/命中率、平均每对话 token（均分「今日 / 累计」两组口径）。
3. **前端展示（`frontend/src/modules/dashboard`）**：新增「AI 用量」区块，4 张汇总卡片（对话总数 / 累计 Token / 缓存命中率 / 平均每对话 Token），每卡展示今日 + 累计。

无 **BREAKING** 变更（纯新增字段 + 新增区块；历史消息 token 仍为 0，口径只对修复后的新消息生效）。

## 关联文档

- `dev_docs/02-PRD需求/PRD-01-仪表盘.md` §2.1（统计概览）、§4（指标口径）、§5.2（stats 端点）
- `dev_docs/03-设计与架构/ARCH-01-仪表盘.md` §3.2（聚合设计）、§5（跨模块只读）
- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.6（SSE 流式对话）、§6（ai_messages 表）

## Capabilities

### New Capabilities

- `dashboard-ai-usage`: 仪表盘统计并展示 AI 助手的 token 用量、对话次数、缓存命中（今日/累计）。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/ai_assistant/models.py`（+2 字段）+ migration、`views/chat_views.py`（捕获用量）、`agent_scope/agent_factory.py`（缓存中间件）、`apps/dashboard/views.py`（`ai_usage` 聚合）
- 前端：`frontend/src/modules/dashboard/`（`DashboardView.logic.ts` / `useDashboardStats.ts` / `index.vue` + 新卡片组件）、`frontend/src/shared/types/dashboard.ts`
- 测试：`manage.py check` + `makemigrations --check` + `ruff` + `pytest`；`gen_arch_stats --check-boundaries`；前端 `npm run typecheck`/`build`；真实对话后仪表盘刷新验证
