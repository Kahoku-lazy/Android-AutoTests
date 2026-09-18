## Context

- 现状（已核实）：`ai_messages` 有 `tokens`/`input_tokens`/`model_name` 字段但恒为 0/空——后端 `_persist_and_forward_terminal` 未传，前端 `onDone` 因 `_backend_msg_id` 存在而跳过保存。缓存命中无字段、无落库。
- AgentScope 2.0.3 能力（已核实源码）：`ModelCallEndEvent` 携带 `input_tokens`/`output_tokens`（无缓存）；`ChatUsage` 有 `cache_creation_input_tokens`/`cache_input_tokens`；`on_model_call` 中间件能拿到完整 `ChatResponse.usage`（含缓存）；`Msg.usage` 仅 input/output（缓存字段被丢弃）。
- 仪表盘是纯只读聚合层（`apps/dashboard/views.py` 386 行），已跨 App 读 `ai_assistant.models.AIAgent`。

## Goals / Non-Goals

**Goals:**

- 后端捕获并落库 AI 消息的输入/输出 token、模型名、缓存命中/写入 token。
- 仪表盘 `stats` 接口新增 `ai_usage` 字段（对话数、输入/输出 token、缓存命中率、平均每对话 token，均分今日/累计）。
- 前端仪表盘新增「AI 用量」区块（4 卡，每卡今日 + 累计）。

**Non-Goals:**

- 不回溯补算历史消息 token（历史恒 0，口径只对新消息生效）。
- 不做每智能体/每对话明细列表（本次只做汇总卡）。
- 不改 AgentScope 第三方源码（只用其官方中间件钩子）。
- 不做 token 计费/成本换算（只统计 token 数）。

## Decisions

**D1：token 语义定为 `input_tokens`=输入、`tokens`=输出（后端成为真相源）。**
`MODEL_CALL_END` 直接给 input/output；前端旧的 `tokens=total` 语义不再生效（后端落库后前端跳过保存）。累计 token = `input_tokens + tokens`。备选：新增 `output_tokens` 字段——被否，复用现有 `tokens` 字段并文档化语义即可。

**D2：token 捕获点在 `chat_views._agent_stream` 事件循环。**
循环中遇到 `MODEL_CALL_END` 累加 `input_tokens`/`output_tokens`，终端持久化时传入 `save_message`（含 `model_name=conv.agent.model_name`）。备选：从 `agent.state.context` 读 `Msg.usage`——被否，需多读一轮上下文且 `Usage` 无缓存字段。

**D3：缓存命中经 `on_model_call` 中间件捕获。**
新增 `UsageCaptureMiddleware`（`MiddlewareBase` 子类），在 `on_model_call` 里 `await next_handler(...)` 拿到 `ChatResponse`，累加 `usage.cache_input_tokens`/`cache_creation_input_tokens` 到 per-session 注册表（沿用 hitl 会话注册表模式）；`_agent_stream` 终端时读取并落库。备选：改 AgentScope 事件/源码——被否（第三方源码不动）。

**D4：DeepSeek 缓存字段 fallback（P1 风险点）。**
DeepSeek API 返回 `prompt_cache_hit_tokens`，而平台 deepseek 走 `OpenAIChatModel`（读 OpenAI `prompt_tokens_details.cached_tokens`）→ 缓存命中会恒 0。方案：子类化 `OpenAIChatModel`，在 usage 转换时同时读 `prompt_cache_hit_tokens` 兜底（保持 openai formatter 以兼容视觉输入）。若验证发现 DeepSeek 视觉模型不返回该字段，则命中率卡显示 0/—（降级）。

**D5：仪表盘新增 `_ai_usage_stats()` 只读聚合，加进 `stats` 响应 `ai_usage` 字段。**
跨 App 读 `ai_assistant.models.AIConversation`/`AIMessage`；今日口径 = `created_at >= 当日 0 点`；`cache_hit_rate = cache_hit_tokens / input_tokens`（除 0 得 0）；`avg_tokens_per_conversation = (input+output) / 对话数`。备选：新开 `/dashboard/ai-usage/` 端点——被否，并入 stats 保持「首页一次拉取」。

**D6：前端新增「AI 用量」区块（平台运营与测试用例之间），4 卡复用 `StatsCard`。**
每卡主值显示累计，副行显示「今日 +N」；缓存命中率用百分比（今日/累计）。字段 snake_case → camelCase 映射。备选：每指标拆今日/累计两张卡——被否，卡片翻倍太挤。

## 模块防火墙自检

- ai_assistant：写库经 `api.save_message` ✅；`UsageCaptureMiddleware` 注册进本 App 的 Agent 构建 ✅；不 import 其他 App 内部实现 ✅。
- dashboard：只读跨 App import `ai_assistant.models.AIConversation`/`AIMessage`（Model 只读 ✅）+ `ai_assistant.api`（如需可见性过滤 ✅）；无写操作 ✅。
- 前端：只消费 `/api/dashboard/stats/` ✅，不直连 DB ✅。

## Risks / Trade-offs

- [缓存命中对 DeepSeek 读不到（字段名不一致）] → D4 子类化兜底 + 验证；失败则命中率 0/—，不阻断其余卡片。
- [历史消息 token 恒 0] → 口径从修复后累计，文档注明；不做回溯补算。
- [dashboard/views.py 已 386 行（>300 上限）] → 本次新增聚合函数，接近 450 行时评估拆 `service.py`。
- [模型流式返回时中间件拿 usage 需处理 AsyncGenerator] → 实现时参考 tracing 中间件的流式包装；若复杂，先按非流式 `ChatResponse` 捕获，实测对齐。
