## Why

知识库助手目前只有语音入口：必须先授权麦克风、开口说话，办公室里、会议室里、外放受限时都没法用；一句「长按开关 3 秒会怎样」也要先对着麦克风讲。本地知识检索已经具备、对话记录面板也已经具备输入框（只是被关掉了），缺的只是一个能打字提问、答案流式出现的文本通道；文本模型用 DeepSeek Flash，比实时语音更便宜也更快。

## What Changes

- **页面新增「语音 / 文字」方式选择**：选好方式再点「开始对话」；一次会话只有一种方式；文字模式不申请麦克风、不建音频播放器；切换方式必须先结束当前会话。
- **复用右侧已有的输入框**：`TranscriptPanel` 已有 composer（当前 `show-composer=false`），文字模式打开它；回答按现有 `reply_start` / `transcript_delta` / `transcript_final` / `reply_end` 事件流式出现，多轮历史在本次连接内保留。
- **同一条 WS 增加 `mode` 与 `text` 消息**：`/ws/knowledge-assistant/?mode=voice|text`；`text` 只在 text 模式生效；连接仍不接 channel layer，仍禁止任何平台写操作。
- **新增 DeepSeek Flash 知识问答角色**：`agent_config.yaml` 增加 `KNOWLEDGE_CHAT_ROLE_CONFIG`，提示词落 `config/data/prompts/KNOWLEDGE_CHAT_PROMPT.md`，装配入口 `build_knowledge_chat()`；RAG 仍用 `search_knowledge` 只读工具，与语音共用同一份索引。
- **状态接口扩展**：新增 `text_model` / `text_ready` / `text_reason`；缺 DeepSeek Key 时只禁用文字入口，不影响语音入口。
- **日志与记账复用**：同一个 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`（`session_start` 带 `mode` 字段），`model_usage` 按 provider=deepseek / category=LLM 记账，账本 `source` 区分 `voice` 与 `chat`。
- **BREAKING（规格契约，不是用户可见行为）**：`/ws/knowledge-assistant/` 不再是「只承载实时语音」；同时退役规格里已无代码支撑的 pipeline / livetranslate 需求（代码早删，规格一直没同步，其中「Pipeline 文本输入」还与本变更的文本协议直接冲突）。
- **不改**：数据库表结构、HTTP 路由、依赖、语音链路行为；语音与文字**不共享**上下文（已确认），切换方式视为开新话题。
- 已知取舍：上一条回答未结束时再次发送会被拒绝并提示（串行处理）；文字模式暂不提供打断 / 取消。

## 关联文档

- PRD：`PRD-平台总需求` 一、1.4 产品边界 第 8 条（知识库助手「本期产品面以语音与平台说明为主」）→ 本期扩为语音 / 文字双入口；五、非功能约束「实时性」（唯一例外通道「只承载音频、转写、打断与播放进度」）→ 改为「知识库问答通道，另承载文字提问」；六、术语「知识库助手」同步。
- 既有规格：`openspec/specs/knowledge-assistant-voice`（本次 MODIFIED / REMOVED 的主要对象）。
- 相关归档变更：`2026-10-28-add-pipeline-text-input`（pipeline 文本输入，源实现已删）、`2026-10-28-default-omni-direct-dialogue`（omni 为唯一路线）、`2026-10-28-refactor-knowledge-assistant-to-engine`（引擎侧落点）。本次把三者最终收敛为「语音 omni + 文字 DeepSeek Flash」两条入口。

## Capabilities

### New Capabilities

- `knowledge-assistant-text-chat`: 文字问答的方式选择、会话协议、模型与检索口径、日志与用量、双入口就绪状态。

### Modified Capabilities

- `knowledge-assistant-voice`: 「页面提供单一语音按键启动会话」「就绪状态可查询」「语音模型 Token 用量记录」「语音 LLM 的 RAG 增强」按双入口改写；「WebSocket 只用于实时语音通道」退役并换成「WebSocket 只承载知识库问答通道」；REMOVED 已删除的 pipeline / livetranslate 需求（实时翻译协议、调用方式可选、前端双路线、Pipeline 问答链路 / 文本输入 / Agent 承担 / 音频整段 / 用量口径 / 链路回退）。

## Impact

- 前端：`frontend/src/modules/knowledge-assistant/`（`index.vue`、`components/VoiceConsole.vue`、`components/TranscriptPanel.vue`、`composables/useVoiceSession.ts`、`constants.ts`、`types.ts`）；新增 `frontend/tests/knowledge-assistant/p0/text-chat.spec.ts`。
- 后端：`backend/apps/knowledge_assistant/consumer.py`（mode 解析、text 白名单、文字会话任务）、`runtime.py`（状态字段）、`transcript_log.py`（`mode` 字段）。
- 引擎：新增 `engines/agents/knowledge_chat/`（配置 + 会话 + AGENTS）；`agent_builders.py`、`role_sys_prompts.py`、`config/data/agent_config.yaml`、`config/data/prompts/KNOWLEDGE_CHAT_PROMPT.md`、`realtime_vocie/events.py`（事件桥接受非语音模型）。
- 记账：`backend/apps/usage_ledger/api.py`（`source` 区分 voice / chat）。
- 文档：PRD 三处；`frontend/src/modules/knowledge-assistant/AGENTS.md`、`backend/apps/knowledge_assistant/AGENTS.md`、`engines/agents/AGENTS.md`、`engines/agents/realtime_vocie/AGENTS.md`。
- 测试：新增 `tests/graybox/unit/test_knowledge_chat_*.py`；扩展 `tests/graybox/unit/test_knowledge_assistant_consumer.py`。
- 非目标：语音与文字共享上下文；文字模式打断 / 取消；新增 HTTP / SSE 文字接口；RAG 运营面（上传 / 解析 / 引用范围）。
