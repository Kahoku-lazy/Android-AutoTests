## Why

AI 助手当前是「单模型 ReAct 隐式路由」：一个 Agent 只挂一个 `model_name`，靠 ReAct 循环自己选工具。但平台有两类截然不同的任务——**控制手机/工作流需要视觉模型「看屏幕像素」，执行用例/闲聊只需文本大模型**——单一模型无法同时胜任。且意图本身是模糊语义（"测试打开APP功能"是用例意图，不是控制手机），必须交给 AI 做语义判断而非关键词规则。因此在 ReAct 之前插入一层 **AI 意图分类 + 双模型路由**，让视觉模型和文本模型各司其职。

## What Changes

1. 新增 AI 意图分类层（`agent_scope/intent_router.py`）：用 `deepseek-v4-pro` 做模糊语义判断，把用户输入归为 4 类意图之一——`phone_control`（控制手机）/ `workflow`（工作流工作台）/ `test_case`（平台用例）/ `other`（其它），输出 `{intent, confidence, reason}`。
2. `AIAgent` 新增 `vision_model_name` 字段：一个 Agent 同时持有文本模型名与视觉模型名。
3. `agent_factory.build_agent` 按意图选执行模型 + 工具子集：
   - `phone_control` / `workflow` → 视觉模型 + 设备/页面流工具子集
   - `test_case` → 文本模型 + 用例/执行工具子集
   - `other` → 文本模型 + **不挂工具**（纯对话）
4. `chat_views._agent_stream` 在 `build_agent` 前先执行意图分类，把意图传入。
5. 前端智能体配置页新增视觉模型下拉框。

无 **BREAKING** 变更（新增字段/文件，现有单一文本模型链路在未配置视觉模型时按 `other`/默认路径降级）。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §4.1（平台业务工具）、§2.6（SSE 流式对话）、§5.2（智能体字段）
- `dev_docs/03-设计与架构/ARCH-08-AI助手.md` §3.2（进程内 Agent 构建）、§3.5（工具双通道）
- `dev_docs/项目笔记/页面结构分析-AI语义增强实现方案.md` §0（AgentScope 2.0.3 机制：thinking 模型不支持强制 tool_choice）
- `apps/dashboard/ai_usage.py`（DeepSeek 双模型计费，路由后自动分开统计）

## Capabilities

### New Capabilities

- `ai-intent-routing`: AI 智能体在对话中按用户输入意图（控制手机 / 工作流 / 平台用例 / 其它）选择视觉模型或文本模型、以及对应的工具子集执行，并支持低置信度澄清。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/ai_assistant/agent_scope/intent_router.py`（新增）、`apps/ai_assistant/models.py`（`AIAgent` 加 `vision_model_name` + 迁移）、`apps/ai_assistant/agent_scope/agent_factory.py`（按意图选模型/工具）、`apps/ai_assistant/views/chat_views.py`（分类接入）、`apps/ai_assistant/serializers.py`（新字段校验）
- 前端：`frontend/src/modules/ai-assistant/AgentDetail.vue` + `helpers/model-config.ts`（视觉模型下拉框）
- 测试：`manage.py check` + `makemigrations --check` + `ruff check` + `pytest`；`python tools/gen_arch_stats.py --check-boundaries`
