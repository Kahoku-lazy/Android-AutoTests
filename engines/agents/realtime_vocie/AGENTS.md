# realtime_vocie 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md`、`engines/AGENTS.md`、`engines/agents/AGENTS.md` 优先于本文件（本文件只写增量）。

## 职责

AgentScope 实时语音助手的**引擎实现**，不承担 HTTP/WS 接入：

| 文件 | 职责 |
| --- | --- |
| `config.py` | `RealtimeVoiceConfig`、环境读取、`build_runtime_status()`、`create_realtime_model()` |
| `knowledge.py` | 直接对话系统提示词（参考 realtime_voice_demo，不注入预设答案） |
| `events.py` | `VoiceLogSink` 协议 + `TranscriptBridge`（AgentScope 事件 → 前端线格式） |
| `session.py` | `RealtimeVoiceSession`：`RealtimeAgent` 生命周期、Omni RAG 工具、就绪事件、看门狗 |
| `livetranslate.py` | `qwen3.8-livetranslate` 实时翻译适配器（session.update / 事件映射 / session.finish） |
| `pipeline.py` | `PipelineVoiceSession`：ASR/文本 → DeepSeek Flash → Sambert/Qwen TTS 的问答会话 |
| `pipeline_llm.py` | `DeepSeekAnswerer`：DeepSeek Flash 流式回答 + 多轮历史 |
| `pipeline_tts.py` | `SambertTts`（默认 sambert-zhichu-v1）/ `QwenTts` → 24kHz PCM16 |
| `transport.py` | `TransportBase` 的浏览器 WebSocket 实现（音频 + 控制帧 + 电平诊断） |

后端接入层在 `backend/apps/knowledge_assistant/`（consumer / runtime / 日志 / 状态接口）。

## 红线

1. **不反向依赖后端**：禁止 `import backend.apps.*`；日志通过 `VoiceLogSink` 协议注入。
2. **异常只用内置类型**：配置/模型错误用 `RuntimeError`；禁止新增自定义异常类。
3. **不写库、不读 Django**：本包只依赖 AgentScope、标准库与 `utils.logs`。
4. **事件契约**：线格式 `type` 与前端 `frontend/src/modules/knowledge-assistant/types.ts` 保持一致；改字段必须双边同步。
5. **不复制提示词到后端**：直接对话提示词只在本包 `knowledge.py` 维护；不得注入平台知识速览或预设答案。Pipeline 的检索资料由 `engines/agents/rag` 提供，仅注入当轮上下文。
6. **调用方式**：`omni`（默认，直接对话）/ `livetranslate`（实时翻译）/ `pipeline`（ASR + DeepSeek Flash + TTS）。前端按连接带 `mode`；默认模型 `qwen3.5-omni-plus-realtime`。
7. **TTS 边界**：`qwen3.8-livetranslate` 输入仅 Audio/Image，不能接收文本做 TTS；pipeline 默认用 `sambert-zhichu-v1`（知厨），可切 `qwen3-tts-flash`。不要把 DeepSeek 文本塞给翻译模型。
8. **会话释放**：`RealtimeVoiceSession` / `PipelineVoiceSession` 必须保证 `session_end` 落盘与看门狗取消。
9. **Token 记录**：Omni 从 `ModelCallEndEvent` 写 `model_usage`；Pipeline 从 DeepSeek `ChatResponse.usage` 写 `model_usage`，ASR 有用量时写 `asr_usage`；`session_end` 必须带 token 汇总。

## 快速验证

```powershell
python -c "import engines.agents.realtime_vocie"
ruff check engines/agents/realtime_vocie
python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_assistant_*.py tests/graybox/unit/test_realtime_vocie_models.py
```
