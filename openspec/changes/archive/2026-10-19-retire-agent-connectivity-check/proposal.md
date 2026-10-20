## Why

「校验」是模型配置页时代的运维辅助：进页对供应商发一轮同步网络探测，把结果写成线路 health 与卡片徽标。配置页已收缩、模型改由后台维护，这套探测只剩一个按钮和一行状态，却仍会在每次进页时阻塞请求、制造误报（余额不足、目录缺失等）。产品决定去掉校验功能。

## What Changes

- **BREAKING（前端）** 卡片删除「校验」按钮与第三行连通徽标，身份区改为「名称 / 职责」两行，底部只保留「配置」。
- 删除进页自动 health 轮询、`testAgent` / `checkAgentsHealth` / `detectModels` 及 `RouteConnStatus` / `RouteHealth` / `AgentTestResponse` / `AgentHealthResponse` 等前端类型。
- **BREAKING（后端）** 删除四个端点：`POST /api/ai/agents/{id}/test`、`GET /api/ai/agents/health/`、`GET /api/ai/agents/{id}/models`、`POST /api/ai/models/detect/`。
- 删除全部探测辅助（两段探测、三态聚合、目录探测、健康缓存判定）与 `api.update_agent_connectivity` / `update_route_connectivity` / `get_route_model_config`。
- **BREAKING（数据）** 删除 `AIAgent.is_connected`、`last_checked_at`、`available_models` 三个字段（一次迁移）；`route_configs.*.health` 的历史 JSON 键保留但不读取。
- 序列化器：详情不再返回三个健康字段；列表的线路摘要不再返回 `health`。
- 文档：模块 AGENTS 卡片描述改为两行 + 仅配置。

## 关联文档

产品口头决策「校验功能去掉」，无 PRD 编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-route-connectivity`: 整个能力退役（两段探测与三态徽标全部移除）。
- `ai-assistant/route-card-identity`: 身份区由三行收为两行；底部操作只保留配置。
- `frontend-doodle-content-card`: 卡片身份不再含连通状态；按钮色调映射去掉「校验」。

## Impact

- 前端：`AgentRouteCard.vue`、`index.vue`、`index.logic.ts`、`api/agents.ts`、`shared/types/ai.ts`、模块 AGENTS。
- 后端：`views_drf.py`、`urls.py`、`api.py`、`models.py`、`serializers.py`；新增一条删字段迁移。
- 数据：`ai_agents` 三个健康列物理删除，**不可逆**。
- 不触碰：`POST /api/ai/agents/{id}/reveal-key`、任务发布链路、引擎装配。
