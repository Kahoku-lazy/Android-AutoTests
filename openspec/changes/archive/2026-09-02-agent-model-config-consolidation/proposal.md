## Why

`add-ai-multi-agent-orchestration` 已把智能体重构为「model + Harness」（4 套 Harness 各自绑定模型），但落库 `AIAgent` 仍只有 `model_name` + `vision_model_name` 两个平铺字段，`strong_model_name` / `strong_enabled` 未落库——强模型 Harness 永远回退到视觉模型；同时前端配置页只暴露到视觉模型，卡片页还残留旧的「单模型快捷切换」（只改 `model_name`），与多 Harness 世界观冲突。需要把模型配置收敛：三类模型（主推理 / 视觉 / 强）统一到配置页管理，卡片只保留「对话 / 配置 / 测试」。

## What Changes

1. 后端 `AIAgent` 新增 `strong_model_name`（强模型名，空则回退视觉模型）与 `strong_enabled`（强模型短路开关，默认 False）两个字段，走迁移。
2. 后端 `serializers.py` 增加两字段校验；`api.py` 读写两字段；`views/chat_views.py` 装配 `AgentManager` 的 config 时传入 `strong_model_name` / `strong_enabled`。
3. 前端配置页（`AgentDetail.vue` + `AgentModelConfig.vue`）把模型配置扩为三类：主推理模型（`model_name`）、视觉模型（`vision_model_name`）、强模型（`strong_enabled` 开关 + `strong_model_name` 下拉，留空回退视觉模型）。
4. 前端卡片（`AgentStickyNote.vue`）移除模型切换行（`model-row`），操作按钮精简为「对话 / 配置 / 测试」。
5. 前端清理快捷切换逻辑：移除 `pendingModels` / `confirmModel` / `getModelOptions` / `hasPendingModelChange` / `updateAgentModel` 及卡片「删除」按钮与 `deleteAgent` 调用。

**BREAKING**：卡片页模型快捷切换入口移除（`POST /ai/agents/{id}/update` 端点保留，供配置页 `saveAgent` 复用）；卡片「删除」按钮移除（平台唯一智能体不再删除，PRD-08 v6.15）。

## 关联文档

- PRD：`dev_docs/02-PRD需求/PRD-08-AI助手.md`（§2.1 智能体看板、§2.2 智能体创建/编辑-模型配置、§4.2 Agent 构建口径）
- ARCH：`dev_docs/03-设计与架构/ARCH-08-AI助手.md`（§3.2 进程内 Agent 构建、§4.2 Agent 详情字段契约）
- UI 规范：无 ai-assistant 专属 UI 规范文档（前端走 Doodle Craft 主题 + `frontend/AGENTS.md` 全局规范）

## Capabilities

### New Capabilities

- `ai-agent-model-config`: 智能体模型配置——三类模型（主推理 / 视觉 / 强）在配置页统一管理，强模型可开关；卡片页收敛为只读展示与「对话 / 配置 / 测试」操作，不再提供模型快捷切换。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/ai_assistant/models.py`（+2 字段）、`migrations/`（新增迁移）、`serializers.py`、`api.py`、`views/chat_views.py`（config 装配）。
- 前端：`frontend/src/modules/ai-assistant/AgentDetail.vue`、`components/AgentModelConfig.vue`（三类模型配置）、`components/AgentStickyNote.vue`（移除 model-row 与删除按钮）、`index.vue`、`index.logic.ts`、`api/agents.ts`、`helpers/model-config.ts`（清理快捷切换逻辑）。
- 测试：`tests/ai_assistant/test_agent_manager.py`（strong 字段装配）、`tests/ai_assistant/test_model_instance.py`（strong 回退）随字段落库同步；前端关单走 `vue-frontend-check`，后端走 `django-backend-check`。
- 依赖：承接 `add-ai-multi-agent-orchestration`（其后端 agent_scope 骨架 + 4 Harness）；该 change 的 design「前端配置页后续跟进」即本 change。
