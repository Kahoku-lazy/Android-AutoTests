## Why

线路卡片点「校验」后显示「已连通」，但发布任务时供应商返回 `402 Insufficient Balance`。根因是连通探测只 GET `/models`（密钥能列目录即视为连通），不等于该模型能推理。用户要求卡片只呈现三种业务状态，且进入看板即探测，不再出现「未检测」。

## What Changes

- 将线路连通探测从「密钥能访问模型列表」提升为两段探测：先验证密钥可达，再对每个已配置角色发极短 `chat/completions`（或等价推理接口）。
- 线路卡片徽标 **BREAKING**（展示文案与状态枚举）：删除「未检测 / 已连通 / 已断开」，仅允许：
  1. 秘钥已连接，但无法使用
  2. 已连通，可执行任务
  3. 连接失败，小助手断线
- 进入智能体看板即触发探测（沿用现有 `GET /ai/agents/health`）；无缓存或缓存缺少新状态字段时必须实探，完成后徽标必落在上述三种之一。探测进行中只允许按钮/徽标显示过程文案「校验中…」，不算第四种业务状态。
- `route_configs.{route}.health` 与 test/health 响应增加线路级三态字段；布尔 `is_connected` 仅表示「可执行任务」那一态，避免旧前端把「密钥通了」当成可用。
- 配置页「校验模型连接」的成功提示与角色行文案对齐同一套判定（不另发明第四态）。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（ai_assistant 为 AI 中枢；外部 LLM HTTP 属于 L0 边界）
- PRD：无独立「线路连通三态」条目；需求来自工作台验收（402 与「已连通」语义冲突）及本变更对话确认（方案 A：进页即探测）
- UI 规范：看板线路卡见 `frontend/src/modules/ai-assistant/AGENTS.md`（实现后需同步删除「未检测」口径）

## Capabilities

### New Capabilities

- `ai-route-connectivity`: 线路连通两段探测、三态落库与看板徽标（进页必有三态之一）

### Modified Capabilities

- （无）`ai-agent-routes` 只覆盖线路模型配置与 Key 脱敏，不描述连通探测；本变更不改其需求。

## Impact

- 后端：`apps/ai_assistant/views_drf.py`（`_test_model_config` / `_test_agent_route` / `test` / `health`）、`apps/ai_assistant/api.py`（`update_route_connectivity`）、`apps/ai_assistant/serializers.py`（health DTO）
- 前端：`AgentRouteCard.vue` 徽标、`index.logic.ts` 水合与 health 应用、`shared/types/ai.ts`、配置页 `AgentDetail.vue` 校验文案
- 契约：`POST /api/ai/agents/{id}/test`、`GET /api/ai/agents/health` 增加线路 `status`（三态）；旧 `connected` / `is_connected` 收紧为「可执行」
- 测试：后端 unit（探测分层与聚合）；前端卡片三态渲染；无新外部依赖
