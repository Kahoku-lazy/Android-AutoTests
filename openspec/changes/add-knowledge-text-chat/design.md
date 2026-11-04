## Context

页面现状（`frontend/src/modules/knowledge-assistant/`）：左栏 `VoiceConsole` 是语音台，右栏 `TranscriptPanel` 负责渲染消息，其 composer 已经存在但被 `:show-composer="false"` 关闭；消息归并由纯函数 `helpers/transcript.ts` 完成，只认 `reply_start` / `transcript_delta` / `transcript_final` / `reply_end` 四类事件。

通道现状（`backend/apps/knowledge_assistant/consumer.py`）：唯一 WS `/ws/knowledge-assistant/?token=…`，不接 channel layer，上行白名单只有 `interrupt` 与 `played`；`connect()` 后立刻起一个 Omni 实时会话。引擎侧 `RealtimeVoiceSession` 用 `TranscriptBridge` 把 AgentScope 事件翻成前端线格式，并写 `logs/knowledge_assistant/YYYY-MM-DD.jsonl` 与 `model_usage`。

关键约束：AgentScope 的 `DashScopeRealtimeModel`（Omni）`supports_text_input = False`——只有 Qwen-Audio 那版实时模型支持文字轮次。所以「打字」无法注入现有语音会话，必须由一个独立的文本模型会话承担。文本链路在全仓尚无多轮实现：`AgentRoleFactory` 每次 `build_*` 只服务单次工作流运行。

模型与提示词现状：`deepseek-flash` 已是 `agent_config.yaml` 里 6 个角色的默认模型；提示词正文在 `config/data/prompts/*.md`，经 `role_sys_prompts` 导出；RAG 已提供 `search_knowledge` 只读工具与 `RagService`。

基线规格 `openspec/specs/knowledge-assistant-voice` 仍在描述已删除的 pipeline / livetranslate（代码早删、规格未同步），其中的「Pipeline 文本输入」还与本变更的 `text` 协议直接互斥——本次一并退役。

## Goals / Non-Goals

**Goals:**

- 打字即可提问，回答流式出现；不申请麦克风、不建播放器。
- 复用同一份本地知识、同一个对话日志、同一本用量账；语音链路零回归。
- 协议向后兼容：不带 `mode` 的连接仍按语音处理。
- 规格与代码对齐：退役 pipeline / livetranslate 需求。

**Non-Goals:**

- 不做语音与文字共享上下文。
- 不做文字模式的打断 / 取消（可结束会话后再重开）。
- 不新增 HTTP / SSE 文字接口，不新增第二条 WS。
- 不做 RAG 运营面，不改动索引与切块口径。

## Decisions

**1. 同一条 WS 上按 `mode` 分流，而不是新开通道。**

备选：新 WS `/ws/knowledge-chat/`（违反「平台唯一 WS 通道」与 `tests/arch` 的通道契约）、HTTP + SSE（平台没有 SSE 先例，且要另建一套流式传输与鉴权）、HTTP 非流式（打字后要干等 3–10 秒，体验最差）。

取 `?mode=voice|text`：旧客户端不传 `mode` → 按语音处理，行为完全不变；新前端切换方式只需重连。

**2. 文字会话 = 一个 AgentScope `Agent` + 复用现有事件桥。**

新增 `engines/agents/knowledge_chat/`（`config.py` + `session.py` + `AGENTS.md`），按 `engines/agents/AGENTS.md`「创建 Agent 统一流程」装配：`agent_config.yaml` 加 `KNOWLEDGE_CHAT_ROLE_CONFIG`（deepseek-flash、stream=true）、提示词落 `KNOWLEDGE_CHAT_PROMPT.md`、`agent_builders.build_knowledge_chat()` 走 `AgentRoleFactory`。

Agent 实例每连接一个 → 多轮历史天然落在 Agent memory，不需要另建会话存储。回答事件直接喂给 `TranscriptBridge`，前端拿到的仍是 `reply_*`，归并逻辑零改动。

备选：直接调 `ChatModelBase` 流式接口——会丢掉重试 / 回退中间件与统一事件流，还要在应用层自己拼 token 用量。

**3. 文字会话关掉 TTS 中间件，RAG 仍用工具。**

`build_agent_middlewares` 默认 `with_tts=True`，文字回答合成语音既无用也费钱，装配时显式 `with_tts=False`。检索走 `search_knowledge` 工具（与 Omni 同一份索引、同一提示纪律），而不是每轮预注入：`max_context_chars=3000` 的片段塞进每轮上下文会显著抬高 token，而很多问题（平台用法）并不需要查资料。

**4. 事件桥参数化 provider / category / model。**

`TranscriptBridge` 目前把 `model_usage` 写死成 `provider=dashscope`、`category=Realtime`；文字会话不经改造会把 DeepSeek token 记成 DashScope 实时花费。改为构造参数（语音保持原值），由既有 `tests/graybox/unit/test_knowledge_assistant_events.py` 守护。

**5. 语音与文字不共享上下文。**

Omni 的历史在模型服务端的会话内，无法导出给 DeepSeek；若把语音转写镜像进文字 Agent 的记忆，要处理重复写、打断截断、乱序到达三类边界，收益（「刚才那个呢」）小于成本。已与用户确认：切方式 = 开新话题。

**6. 前端复用 composer，只加方式选择。**

左栏加两枚 `DoodleBtn`（语音 / 文字）作为方式选择，文字模式隐藏麦克风选择与电平区，状态文案切到「正在思考…」「正在回答…」；右栏把 `showComposer` 打开，`canSend` 由「文字模式 + 连接就绪 + 无进行中的回答」推导。不新增组件、不新增第二套样式皮肤。

备选：输入即自动建连——与「打开页面不主动建连」的既有规格冲突，且语音进行中抢通道的语义不清。

**7. 一次只处理一条文字消息。**

生成中再发被拒绝并提示「上一条还在回答」，不排队：排队会让用户以为消息丢了，也会让后到的回答与屏幕顺序对不上。文字长度上限 2000 字符（常量集中管理）。

**8. 就绪状态按入口分开。**

状态接口在既有 `ready/reason/model/voice` 之外返回 `text_model` / `text_ready` / `text_reason`；缺少 `DEEPSEEK_API_KEY` 只让文字入口不可用。前端按所选方式显示对应入口的原因。

**9. 一并退役 pipeline / livetranslate 需求。**

它们已无代码支撑，且「Pipeline 文本输入」与本变更互斥。留着会让后续读者按错误规格实现。退役不产生代码改动（代码早已删除）。

## 模块防火墙自检

- 跨 App import：只新增对 `backend.apps.usage_ledger.api.record_voice_event` 的既有调用（消费方），并在该 api 内加 `source` 参数；不 import 其它 App 的 service / consumer / state_machine。
- 写库路径：`knowledge_assistant` 不直接写 `ModelUsage`，仍经 `usage_ledger/api.py`；本变更无新表、无 migrations。
- 前端不直连数据库 / 不直连模型服务商：浏览器只连本平台 WS 与 `/api/`。
- engines 边界：新增 `engines/agents/knowledge_chat` 只依赖 agentscope 与 `engines.agents.*`，零 `django` / `apps.*` 引用。
- 通道边界：仍单连接、仍不接 channel layer、仍不承载任何平台写操作。

## Risks / Trade-offs

- [事件桥参数化漏改语音路径，记账串味] → bridge 构造参数默认值保持语音原值，并让既有 events 单测断言 provider/category 不变。
- [语音连接收到 `text` 被误解] → consumer 按连接 `mode` 分流，语音模式显式忽略；补 consumer 单测。
- [Agent 记忆随轮次增长] → 由 `ContextConfig` 压缩；V1 不额外限制轮数，日志里 `model_usage` 可观察 token 膨胀。
- [无法打断文字回答] → 明确列为非目标；页面在回答中禁用发送，用户可结束会话。
- [规格退役被误读为功能回退] → proposal 与 REMOVED 的 Reason / Migration 都写明「代码早已移除」，并指向新的双入口要求。

## Migration Plan

1. 配置先行：`KNOWLEDGE_CHAT_ROLE_CONFIG` 与 `KNOWLEDGE_CHAT_PROMPT.md` 落地，缺 `DEEPSEEK_API_KEY` 时只影响文字入口。
2. 引擎 → 后端 → 前端按序发布；协议向后兼容，旧前端不发 `text`，旧后端不识别 `mode`（新前端与后端同批发布，不承诺跨版本混跑）。
3. 回滚：前端隐藏文字方式即可停止使用；后端保留 `mode` 解析，语音路径不受影响。无数据迁移，无 schema 变更。
