## 1. 引擎包

- [x] 1.1 新建 `engines/agents/realtime_vocie/__init__.py`、`config.py`、`knowledge.py`、`events.py`、`session.py`、`transport.py`，使用引擎层注释格式；验证：`python -c "import engines.agents.realtime_vocie"` 成功。
- [x] 1.2 `config.py` 去除自定义 `ConfigError` 与 `log_dir`，改用 `RuntimeError` 并提供 `build_runtime_status()`；验证：单测断言缺 Key/关闭/非法 VAD 均抛 `RuntimeError`。
- [x] 1.3 `events.py` 用 `VoiceLogSink` 协议替换后端 `DialogueLog` 依赖；验证：事件桥单测仍通过，且 `grep` 无 `backend.apps` import。
- [x] 1.4 `session.py` / `transport.py` 迁移并用 `agent_event_log`；验证：`grep` 无后端 App import，会话单测/真实 WAV 链路通过。

## 2. 后端接入层

- [x] 2.1 新增 `backend/apps/knowledge_assistant/runtime.py`：`session_log_dir()` 与 `build_status_payload()`；验证：状态接口仍返回 `log_dir/log_file` 且不含密钥。
- [x] 2.2 `consumer.py` 改为 import 引擎 `load_config` / `RealtimeVoiceSession`，捕获 `RuntimeError`，日志目录改由 `runtime.session_log_dir()` 提供；验证：WS 鉴权集成测试通过。
- [x] 2.3 `views.py` 改 import `runtime.build_status_payload`；删除后端 `config.py`、`knowledge.py`、`events.py`、`session.py`、`transport.py`；验证：`manage.py check` 通过。
- [x] 2.4 删除空目录 `engines/agents/realtime_voice`，保留 `realtime_vocie`；验证：目录列表只有 `realtime_vocie`。

## 3. 测试与文档

- [x] 3.1 更新 `tests/graybox/unit/test_knowledge_assistant_*.py` 的 import 与异常断言；验证：相关 pytest 全绿。
- [x] 3.2 更新 `backend/apps/knowledge_assistant/AGENTS.md`，新增 `engines/agents/realtime_vocie/AGENTS.md` 说明边界；验证：文档路径与实现一致。
- [x] 3.3 后端 `ruff check` / `ruff format --check` / `manage.py check`；前端 `npm run typecheck` / `build`；验证：全绿。
- [x] 3.4 真实链路回归：WAV 假麦克风跑通，`audio_probe`/`session_end` 仍有 `audio_frames`；验证：日志与页面正常。
- [x] 3.5 `openspec validate refactor-knowledge-assistant-to-engine --strict` 并归档；验证：通过。

## 4. 验证记录

- 引擎 import：`import engines.agents.realtime_vocie` 成功；`grep` 确认引擎包无 `backend.apps.*` import。
- 后端：`manage.py check` 通过；`ruff check` / `ruff format --check` 覆盖 `backend/apps/knowledge_assistant` 与 `engines/agents/realtime_vocie`；知识库助手相关 pytest **35 passed**。
- 架构边界：`python utils/gen_arch_stats.py --check-boundaries` → **零违规**；OpenAPI `spectacular --validate` 无错误。
- 真实链路：WAV 假麦克风跑通（33 个事件、2 条转写）；浏览器假麦克风跑通并显示用户/助手两条消息与日志路径。
- 目录：`engines/agents/realtime_vocie/` 为唯一语音引擎包；空目录 `realtime_voice` 已删除。
