## 1. 引擎：DeepSeek Flash 知识问答角色

- [x] 1.1 `engines/agents/config/data/agent_config.yaml` 增加 `KNOWLEDGE_CHAT_ROLE_CONFIG`（provider=deepseek、model_name=deepseek-flash、stream=true、vision=false、`system_prompt: KNOWLEDGE_CHAT_PROMPT`）；新增 `config/data/prompts/KNOWLEDGE_CHAT_PROMPT.md`，并在 `role_sys_prompts.py` 增加 `KnowledgeChatPrompts` 导出。验证：`python -c "from engines.agents.role_sys_prompts import KnowledgeChatPrompts; print(len(KnowledgeChatPrompts.system()))"` 能取到正文。 实测：388 字符；`load_role_spec('KNOWLEDGE_CHAT_ROLE_CONFIG')` 得到 `knowledge_chat_role`。
- [x] 1.2 `engines/agents/agent_builders.py` 增加 `build_knowledge_chat()`：走 `_agent_from_role_bundle(load_role_spec("KNOWLEDGE_CHAT_ROLE_CONFIG"), toolkit=…)`，中间件显式 `build_agent_middlewares(fallback_model=…, with_tts=False)`。验证：新单测断言装配出的 Agent 不带语音合成中间件。 实测：`test_chat_agent_has_no_tts_middleware` 通过，`agent.name=knowledge_chat_role`。
- [x] 1.3 新增 `engines/agents/knowledge_chat/`：`config.py`（按角色键取模型名、文本长度上限、就绪判定 `text_ready/text_reason`）、`session.py`（`KnowledgeChatSession`：持有 Agent + `TranscriptBridge`，`answer(text)` 逐条产出与语音同构的线格式事件；RAG 用 `Toolkit(tools=[build_rag_tool(RagService.from_env())])`、`AGENTS.md`。验证：`python -c "from engines.agents.knowledge_chat import KnowledgeChatSession"` 可导入。
- [x] 1.4 `engines/agents/realtime_vocie/events.py`：`TranscriptBridge` 的 `provider` / `category` 改为构造参数（默认 dashscope / Realtime，语音路径零改动），文字会话传 deepseek / LLM。验证：既有 `tests/graybox/unit/test_knowledge_assistant_events.py` 全绿，且新增断言文字会话写出 `provider=deepseek`。
- [x] 1.5 新增 `tests/graybox/unit/test_knowledge_chat_session.py`：用假模型覆盖「多轮引用上一轮」「model_usage 记账字段」「无 usage 不写伪造 0」「检索不可用仍能回答」。验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_chat_session.py -q` 全绿。 实测：7 passed；连同 events/config 共 22 passed。

## 2. 后端：通道分流与状态

- [x] 2.1 `backend/apps/knowledge_assistant/consumer.py`：解析 `?mode=voice|text`（缺省 voice，非法值回可读错误并关闭）；text 模式不起 Omni 会话，收到 `{"type":"text"}` 时校验非空与长度上限后串行处理，生成中再发回 `notice` 拒绝；用完写 `session_end`。验证：扩展 `tests/graybox/unit/test_knowledge_assistant_consumer.py`，覆盖 mode 解析、语音模式忽略 text、超长与空白被拒。 实测：10 passed。
- [x] 2.2 `backend/apps/knowledge_assistant/runtime.py`：`build_status_payload()` 增加 `text_model` / `text_ready` / `text_reason`，缺 DeepSeek Key 时只影响文字入口。验证：新增状态单测断言两组字段互不影响。 实测：`test_status_payload_has_text_fields` 通过。
- [x] 2.3 `backend/apps/usage_ledger/api.py`：`record_voice_event` 增加 `source` 参数（默认 `voice`），文字会话传 `chat`；`event_id` 前缀同步区分。验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_usage_ledger.py -q` 全绿。 实测：6 passed。
- [x] 2.4 确认 `transcript_log.py` 的 `session_start` 能带上方式字段（文字会话写 `mode=text`），不需要改表结构。验证：单测断言当日 JSONL 的 `session_start` 含 `mode`。 实测：`test_session_start_records_mode` 通过。

## 3. 前端：方式选择与文字会话

- [x] 3.1 `types.ts` / `constants.ts`：新增 `AssistantMode = "voice" | "text"`、文字模式的状态文案、`KB_TEXT_MAX_LEN`、`KB_MODE_TEXT`、composer 占位文案与「上一条还在回答」提示。验证：`npm run typecheck` 通过。 实测：另加 `helpers/mode.ts`（模式/状态文案与发送门控的纯函数）。
- [x] 3.2 `composables/useVoiceSession.ts` 扩为双模式：`start(mode)`（text 模式不建 `AudioPlayer` / `MicCapture`，WS 带 `mode=text`）、`submitText(text)`、`canType`（文字模式 + 已连接 + 无进行中回答）。验证：新增 `frontend/tests/knowledge-assistant/p0/text-chat.spec.ts` 覆盖模式参数与发送门控。 实测：5 passed。
- [x] 3.3 `components/VoiceConsole.vue` + `VoiceConsole.style.css`：加「语音 / 文字」两枚方式按钮；文字模式隐藏麦克风选择与电平区，模式行显示「文字问答」。验证：`npx vitest run knowledge-assistant` 与 `npm run lint:styles` 通过。 实测：19 passed；`lint:styles` 对本模块 0 违规（仅 task-list 存量 G6 借用）。
- [x] 3.4 `components/TranscriptPanel.vue`：`showComposer` / `canSend` 接真值，占位文案区分模式，保持组件不含解析逻辑。验证：单测断言 composer 在文字模式可见、语音模式禁用。 实测：门控在 `canSendText` 上单测；输入框加 `maxlength=KB_TEXT_MAX_LEN`。
- [x] 3.5 `index.vue`：按方式编排（开始 / 结束 / 发送），沿用 `messages.length` 滚动到底；文字模式状态文案与语音区分。验证：`npm run typecheck` + `npx vitest run knowledge-assistant`。 实测：两者均通过。

## 4. 文档与红线

- [x] 4.1 PRD 三处同步：一、1.4 第 8 条（语音 + 文字双入口）、五、非功能约束「实时性」（通道改称知识库问答通道）、六、术语「知识库助手」。验证：`grep -n "唯一例外" dev_docs/ARCH_PRD/PRD-平台总需求.md` 只剩语音与文字两类描述。 实测：另同步 `ARCH-平台架构设计.md` §3.3 的通道描述。
- [x] 4.2 三处 AGENTS 改写：`frontend/src/modules/knowledge-assistant/AGENTS.md`（第 6 条红线改为「禁 pipeline 路线，文字问答走 mode=text」）、`backend/apps/knowledge_assistant/AGENTS.md`（WS 白名单加 `text` 与仅文字模式生效）、`engines/agents/AGENTS.md` 与 `realtime_vocie/AGENTS.md`（新增 `knowledge_chat` 包职责）。验证：四份文件与实现一致，无「不得重新引入文本输入框」的过时表述。 实测：另新增 `engines/agents/knowledge_chat/AGENTS.md`。

## 5. 门禁与验收

- [x] 5.1 `python run.py check` 阻塞项全绿（重点：`ruff`、`prettier`、`vue-file-size`、`engines-agents-style` 告警不新增）。 实测：22/22 通过；`engines-agents-style` 仍是存量 25 条 `raises-doc`（全部在 `engines/device`），本变更 0 新增。
- [x] 5.2 目标测试：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_chat_session.py tests/graybox/unit/test_knowledge_assistant_consumer.py tests/graybox/unit/test_knowledge_assistant_events.py -q` 与 `cd frontend && npx vitest run knowledge-assistant` 全绿。 实测：后端 7+10+9 全绿；前端 19 passed。
- [x] 5.3 手工验收（需真实 `DEEPSEEK_API_KEY`）：文字方式打字提问 → 用户消息与流式回答出现、多轮追问生效；检查当日 JSONL 的 `session_start.mode=text`、`model_usage` 的 provider/model、账本 `source=chat`；切回语音确认原链路未回归；生成中再次发送得到拒绝提示。 实测（本机运行中的平台 + 真实 DeepSeek）：`mode=text` 连接 ready→用户回显→26 段 `transcript_delta`→回答「长按 3 秒…进入网络待机模式」；同一连接追问「我刚才问的是什么？」能复述首轮问题；JSONL 有 `session_start.mode=text`、两条 `model_usage(provider=deepseek, model=deepseek-flash)` 与 `session_end` token 汇总；账本新增 `source=chat`、`category=LLM`、`pricing_status=priced`。语音回归见既有 9 条 events/config 单测与 `test_knowledge_assistant_ws.py`。
- [x] 5.4 归档前自查：`openspec validate add-knowledge-text-chat --strict` 仍通过，且 tasks 全部勾选。
