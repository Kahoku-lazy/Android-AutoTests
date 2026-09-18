## Context

动机见 proposal.md - Why。当前状态（已核对源码）：

- `AIAgent` 只落库 `model_name` + `vision_model_name`（`models.py:22-24`），无 `strong_model_name` / `strong_enabled`。
- `agent_manager._build` 的 strong Harness 读 `config.get("strong_model_name")` / `config.get("strong_enabled")`，但 `chat_views._build_manager` 只传 `model_name` + `vision_model_name`（`chat_views.py:455-458`），故强模型永远回退视觉模型、开关永远 False。
- 前端卡片 `AgentStickyNote.vue` 有 `model-row` 快捷切换（只改 `model_name`），配套 `pendingModels` / `confirmModel` / `getModelOptions` / `updateAgentModel`（`index.logic.ts` + `api/agents.ts` + `helpers/model-config.ts`）。
- 前端配置页 `AgentModelConfig.vue` 只有主模型 + 视觉模型（+ provider / key / base_url）。

## Goals / Non-Goals

**Goals:**

- 补齐 `strong_model_name` + `strong_enabled` 落库与装配，让强模型 Harness 可配置、可开关。
- 配置页把模型配置扩为三类：主推理 / 视觉 / 强（强 = 开关 + 下拉）。
- 卡片收敛为「对话 / 配置 / 测试」，移除模型切换与删除。

**Non-Goals:**

- 不改 `agent_manager.py` / `model_instance.py` 的运行时路由逻辑（4 Harness 已实现）。
- 不改 provider / api_key / base_url 的配置方式（三类模型仍共用同一套凭据与 provider）。
- 不删后端 `delete_agent` api 与 `/ai/agents/{id}/delete` 端点（PRD-08 §5.1 仍列 delete）。
- 不解决配置页 provider 列表（`AgentDetail.vue` 硬编码 vs PRD「6 提供商含 gemini」）的既有不一致。

## Decisions

1. **`strong_model_name` + `strong_enabled` 作为 `AIAgent` 平铺字段**（与 `vision_model_name` 同层），不走 JSON 存「每 Harness 一套模型」。
   - 理由：与现有 `model_name` / `vision_model_name` 平铺风格一致、迁移最小；`agent_manager` 的 config dict 已按 `config.get("strong_model_name")` / `config.get("strong_enabled")` 读取，只需落库 + 传入即可生效。
   - 备选：JSON 字段存 4 Harness 各自 model_name（更灵活，但 `agent_manager` 当前不读该结构，属过度设计）。

2. **三类模型映射**：主推理 = `model_name`（intent + reasoning 共用）、视觉 = `vision_model_name`、强 = `strong_model_name`。
   - 理由：对齐 `agent_manager._build` 实际实现（intent/reasoning 用 `model_name`，vision 用 `vision_model_name` 回退 `model_name`，strong 用 `strong_model_name` 回退 `vision_model_name`）。
   - 备选：intent 单独一个模型（设计定稿曾写「每 Harness 一个 model_name」），但实现已收敛为 intent 与 reasoning 共用 `model_name`，本次对齐实现。

3. **强模型 UI = 「启用强模型」开关 + 强模型下拉**，下拉留空回退视觉模型（下拉 placeholder 注明）。
   - 理由：用户已确认「开关 + 下拉」；`strong_enabled` 对应 `is_strong_enabled` 短路，`strong_model_name` 留空走 `agent_manager` 的回退链。
   - 备选：仅下拉留空即不启用（用户已否决）。

4. **卡片移除 `model-row` + 「删除」按钮**，只留「对话 / 配置 / 测试」。
   - 理由：用户要求「卡片只需要有对话，配置，测试」；PRD-08 v6.15 平台唯一智能体不再删除。
   - 前端连带清理：`pendingModels` / `confirmingId` / `confirmModel` / `hasPendingModelChange` / `getModelOptions` / `updateAgentModel` / `deleteAgent`（`index.logic.ts`）+ `api/agents.ts` 的 `updateAgentModel` / `deleteAgent` + `helpers/model-config.ts`（仅被卡片切换消费，删除）。

5. **后端 `update` 端点保留**（配置页 `saveAgent` 复用 `POST /ai/agents/{id}/update`），仅移除前端「单字段快捷更新」专用函数 `updateAgentModel`。
   - 理由：配置页保存仍需完整 update 契约；快捷切换才是本次移除对象。

6. **`chat_views._build_manager` 的 config 增传 `strong_model_name` / `strong_enabled`**，`serializers`（输入 + 详情 DTO）与 `api.create_agent` / `api.update_agent` 同步两字段。
   - 前端 `shared/types/ai.ts` 的 `AgentRecord` 增加可选 `strong_model_name?` / `strong_enabled?`（契约对齐；卡片不展示，但详情 DTO 对齐）。

## 模块防火墙自检

- 后端只改 `apps/ai_assistant` 内的 `models.py` / `serializers.py` / `api.py` / `views/chat_views.py`，无新增跨 App import；写库（`create_agent` / `update_agent`）仍收敛在 `api.py`。
- `chat_views.py` 的 `_build_manager` 只读 `AIAgent` 字段 + 调 `agent_scope`，不写库、不越层。
- 前端只改 `ai-assistant` 模块内组件与 `api/agents.ts`（经 `djangoClient` → `/api/...` DRF），不新增 HTTP 客户端、不直连后端端口、不新增 WS/SSE 通道。
- 结论：不触碰防火墙红线；无新增跨模块依赖。

## Risks / Trade-offs

- [强模型开启但 `strong_model_name` 与 `vision_model_name` 均空 → strong Harness 的 model_name 为空] → 这是 `agent_manager` 既有回退链（strong 不回退 `model_name`）的边界；本次不改 `agent_manager`，配置页强模型下拉留空时依赖视觉模型已配，作为已知边界记录，不强改运行时逻辑。
- [删除 `helpers/model-config.ts` 可能影响其他引用] → 实施前 `grep getModelOptions|BUILTIN_MODELS` 确认无其他消费者再删。
- [卡片移除「删除」后超管无法经 UI 删智能体] → 符合 PRD-08 v6.15「不再删除」；后端端点保留，必要时经 admin 操作。
- [后端详情 DTO 新增两字段，前端/契约需双边同步] → `AgentDetailSerializer` 输出 `strong_model_name` / `strong_enabled`，前端 `AgentRecord` 类型与 `AgentDetail.vue` form 同步；关单走 `django-backend-check` + `vue-frontend-check`。
- [迁移新增字段，需保证默认值安全] → `strong_model_name` 默认空、`strong_enabled` 默认 False，历史数据不启用强模型，行为无回归。
