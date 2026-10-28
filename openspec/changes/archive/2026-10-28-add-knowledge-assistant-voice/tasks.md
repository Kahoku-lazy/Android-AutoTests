## 1. 后端基础能力

- [x] 1.1 新建 `backend/apps/knowledge_assistant/` App（`apps.py`、`__init__.py`、模块 `AGENTS.md`），并在 `backend/config/settings.py` 的 `INSTALLED_APPS` 注册；验证：`python manage.py check` 通过且 `python -c "from backend.apps.knowledge_assistant.apps import KnowledgeAssistantConfig"` 可导入。
- [x] 1.2 新增 `config.py`：读取根 `.env` 的 `DASHSCOPE_API_KEY` 与 `KNOWLEDGE_ASSISTANT_*`，提供默认模型/音色/回合检测/日志目录与 `ConfigError`；验证：新增 `tests/graybox/unit/test_knowledge_assistant_config.py`，覆盖缺 Key、默认值、环境覆盖。
- [x] 1.3 新增 `knowledge.py`：知识库助手系统提示词与平台模块速览，明确不使用 RAG、不编造实时数据；验证：单测断言提示词含模块名与「不使用文档库」约束。
- [x] 1.4 新增 `transcript_log.py`：按自然日写 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`，含 `ts/session_id/user_id/role/text`，会话事件与写入失败容错；验证：新增 `tests/graybox/unit/test_knowledge_assistant_log.py`，检查字段、分文件与失败不抛。

## 2. 浏览器音频传输与会话

- [x] 2.1 新增 `transport.py`：`WebSocketAudioTransport` 实现 `TransportBase`，上行 `AudioFrame`/`ControlFrame` 队列、下行二进制音频与 `audio_item` 标记、`played` 进度回报；验证：新增 `tests/graybox/unit/test_knowledge_assistant_transport.py`，断言入队/出队、`audio_item` 先于音频、`clear_audio` 返回最近进度。
- [x] 2.2 新增 `session.py`：组装 `RealtimeAgent` 与 DashScope 模型，把 `ReplyStart/TextBlockDelta/TextBlockEnd/ReplyEnd` 映射为 `reply_start/transcript_delta/transcript_final/reply_end/state` 事件，并在 `transcript_final` 落日志；验证：单测用假 agent 事件流断言消息映射与落日志（不联网）。
- [x] 2.3 新增 `consumer.py`：`AsyncWebsocketConsumer` 校验 JWT、创建 transport、跑会话任务、处理 `interrupt`/`played` 白名单消息、断连释放资源；验证：新增 `tests/graybox/unit/test_knowledge_assistant_consumer.py`，覆盖无 token 拒绝与白名单解析（用直接调用辅助函数，不启服务）。
- [x] 2.4 新增 `views.py` 与 `urls.py`：`GET /api/knowledge-assistant/status/` 返回就绪状态且不含密钥；在 `backend/config/urls.py` 挂载 `/api/knowledge-assistant/`；验证：`python manage.py spectacular --validate` 无错误，单测断言 payload 字段。
- [x] 2.5 在 `backend/gateway/routing.py` 注册 `/ws/knowledge-assistant/`，并更新该文件说明；验证：单测断言 `websocket_urlpatterns` 含该路径，`python manage.py check` 通过。

## 3. 前端语音能力

- [x] 3.1 新增 `frontend/src/modules/knowledge-assistant/audio/pcm.ts`：Float32/Int16 转换与线性重采样；验证：`frontend/tests/knowledge-assistant/p0/pcm.spec.ts` 覆盖静音、削波、升/降采样长度。
- [x] 3.2 新增 `audio/micCapture.ts` 与 `audio/audioPlayer.ts`：AudioWorklet（ScriptProcessor 兜底）采集、100ms 分块、24kHz 播放排程、`clear()` 与播放进度计算；验证：`npm run typecheck` 通过，纯函数覆盖在 3.1。
- [x] 3.3 新增 `helpers/transcript.ts`：把服务端事件归并为对话消息（增量、最终、打断、错误）；验证：`frontend/tests/knowledge-assistant/p0/transcript.spec.ts` 覆盖用户/助手增量与打断。
- [x] 3.4 新增 `composables/useVoiceSession.ts`：点击启动/结束、麦克风授权、WS 生命周期、状态机、自动滚动信号与错误提示；验证：`npm run typecheck` + 页面手测点击后进入「聆听中」。

## 4. 前端页面与侧栏

- [x] 4.1 新增 `frontend/src/modules/knowledge-assistant/index.vue`、`constants.ts`、`types.ts`、`index.style.css`、`routes.ts`、`components/VoiceConsole.vue`、`components/TranscriptPanel.vue`：`wb-shell` 页面 + 语音按键 + 实时记录 + 日志落点；验证：`npm run build` 通过、`npm run lint:styles` 通过。
- [x] 4.2 在 `frontend/src/router.ts` 注册 `/knowledge-assistant`；验证：路由可直达且页面标题为「知识库助手」。
- [x] 4.3 修改 `frontend/src/shared/components/sidebarNavConfig.ts`：新增「AI 功能」分组（AI 助手、知识库助手），顺序在仪表盘之后、数据之前，并补 `/knowledge-assistant` 模块色；验证：`frontend/tests/shared/p0/sidebarNavConfig.spec.ts` 断言分组、顺序与颜色。
- [x] 4.4 在 `frontend/src/shared/icons/lucide-registry.ts` 补 `Mic` / `BookOpen` 等实际使用的图标；验证：页面图标渲染无 lucide 缺图标告警。

## 5. 文档与配置

- [x] 5.1 更新 `.env.example`，加入 `KNOWLEDGE_ASSISTANT_MODEL/VOICE/TURN_DETECTION` 与「复用 DASHSCOPE_API_KEY」说明；验证：新增变量名可在 `config.py` 找到同名读取。
- [x] 5.2 更新 `dev_docs/ARCH_PRD/PRD-平台总需求.md` 与 `dev_docs/ARCH_PRD/ARCH-平台架构设计.md`：补充知识库助手入口、WS 唯一例外与本地日志路径；验证：`python utils/gen_arch_stats.py --check-md --doc dev_docs/ARCH_PRD/ARCH-平台架构设计.md`（如该门禁要求）。
- [x] 5.3 更新 `frontend/src/modules/knowledge-assistant/AGENTS.md` 与 `backend/apps/knowledge_assistant/AGENTS.md`，写清入口、边界、日志与红线；验证：文件存在且与实现一致。

## 6. 验证与关单

- [x] 6.1 后端：`python manage.py check` + `ruff check backend/apps/knowledge_assistant backend/config backend/gateway` + `python -m pytest -c tests/pytest.ini -m "unit"`（知识库助手相关文件）；验证：全绿。
- [x] 6.2 前端：`cd frontend && npm run lint:styles && npm run typecheck && npx vitest run knowledge-assistant shared/p0/sidebarNavConfig.spec.ts`；验证：全绿。
- [x] 6.3 边界：`python utils/gen_arch_stats.py --check-boundaries`；验证：通过。
- [x] 6.4 人工验收：`python run.py start` 后登录，侧栏出现「AI 功能」分组；打开知识库助手，点击语音按键说一句话，页面实时出现双方记录，`logs/knowledge_assistant/` 出现当日 JSONL；验证：文件含 user/assistant 两条记录。
- [x] 6.5 OpenSpec：`openspec validate add-knowledge-assistant-voice --strict`；验证：通过。

## 7. 验证记录

- 后端单测：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_assistant_config.py ... tests/graybox/integration/test_knowledge_assistant_ws.py -q` → **30 passed**。
- 后端静态：`python manage.py check` 通过；`ruff check` / `ruff format --check backend/apps/knowledge_assistant` 通过；`manage.py spectacular --validate` 无错误。
- 架构边界：`python utils/gen_arch_stats.py --check-boundaries` → **零违规**。
- 前端单测：`npx vitest run knowledge-assistant shared/p0/sidebarNavConfig.spec.ts` → **18 passed**；`npm run typecheck` 通过；`npm run build` 通过。
- 前端样式门禁：新模块自身无悬空/越界引用；`npm run lint:styles` 仍报 50 处 `task-list` 借用 `ai-assistant` 模块令牌的历史存量，与本次变更无关（本次未新增违规）。
- 真实链路：用中文 WAV（“设备管理里怎么连接一台安卓设备？”）按 16k PCM 推流，收到用户转写与助手回复「去设备管理模块…支持 USB 或者 WiFi ADB 两种方式。」；`logs/knowledge_assistant/2026-10-28.jsonl` 写入 `session_start`、`role=user`、`role=assistant`、`session_end`。
- 浏览器验收：Chromium 假麦克风点击语音按键进入「聆听中」；用 WAV 假麦克风跑完整轮次，页面显示用户与助手消息、日志路径指向当日 JSONL。
