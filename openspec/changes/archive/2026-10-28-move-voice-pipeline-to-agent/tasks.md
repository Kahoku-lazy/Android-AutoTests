## 1. 实现

- [x] 1.1 `engines/agents/realtime_vocie/tts_model.py`：`LocalTtsModel(TTSModelBase)`，`synthesize` 调现有引擎并把 PCM 包成一块 `DataBlock`（`audio/pcm;rate=<采样率>`）
- [x] 1.2 `engines/agents/realtime_vocie/agent_answerer.py`：`AgentAnswerer` 消费 `reply_stream`，映射文本增量 / 音频增量 / token 用量，`take_audio()` 取走整段 PCM
- [x] 1.3 `engines/agents/middleware/assembly.py`：`build_agent_middlewares()` 增 `with_tts`（语音链路自带 TTS 时关掉全局 TTS）与 `extra`（自带中间件插在重试之前）
- [x] 1.4 `engines/agents/realtime_vocie/config.py`：`pipeline_engine` 字段 + `KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE` 解析，默认 `agent`，非法值抛 `RuntimeError`
- [x] 1.5 `engines/agents/realtime_vocie/pipeline.py`：新增 `_create_agent_answerer()`（DeepSeek 模型 + `build_agent_middlewares(with_tts=False, extra=[RAG?, TTSMiddleware(LocalTtsModel)])`）；`_answer` 在 Agent 模式下用 `take_audio()` 取代 `self._tts.synthesize(full)`；类型注解扩为 `DeepSeekAnswerer | AgentAnswerer`

## 2. 验证

- [x] 2.1 `tests/graybox/unit/test_voice_agent_answerer.py`（9 例）：文本增量映射、音频增量解码拼接、取走后清空、坏 base64 跳过、token 用量、`LocalTtsModel` 返回单块 PCM / 空音频返回空内容、配置默认 `agent`、可切 `legacy`、非法值报错且点名变量
- [x] 2.2 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_voice_agent_answerer.py tests/graybox/unit/test_agent_middleware_assembly.py -q` → **29 passed**
- [x] 2.3 `python -c "import engines.agents.realtime_vocie.pipeline"` → 导入通过
- [x] 2.4 `ruff format` / `ruff check`（`engines/agents/realtime_vocie`、`engines/agents/middleware`、新测试）→ 通过
- [x] 2.5 `npx openspec validate move-voice-pipeline-to-agent --strict` 通过
- [ ] 2.6 真机验收：语音链路需要真实麦克风与 DashScope 密钥，单测覆盖不到音质与时延 —— 留待你在本机连一次 pipeline 模式确认
