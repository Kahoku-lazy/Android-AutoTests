## Why

需要核对语音助手的模型成本。AgentScope 的 `ModelCallEndEvent` 已包含 `input_tokens` / `output_tokens` / 缓存 token；Pipeline 的 DeepSeek `ChatResponse.usage` 也有 token 数，但当前事件桥与日志都没有记录。

## What Changes

- Omni：`TranscriptBridge` 处理 `ModelCallEndEvent`，写 `model_usage` 事件并累计本次会话 token。
- Pipeline：`DeepSeekAnswerer` 保存最后一次 `ChatResponse.usage`；`PipelineVoiceSession` 写 `model_usage` 并累计。
- `session_end` 增加 `input_tokens` / `output_tokens` / 缓存 token 汇总。
- ASR 的 `ResponseDoneEvent` 也记录 token（如有）。
- 不向前端新增 UI；记录写 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`。

## 关联文档

- 已归档 `2026-10-28-add-rag-voice-llm`
- AgentScope `ModelCallEndEvent`

## Capabilities

### Modified Capabilities

- `knowledge-assistant-voice`: 新增语音模型 token 用量记录。

## Impact

- 引擎：`events.py`、`session.py`、`pipeline_llm.py`、`pipeline.py`。
- 后端/前端：无接口/UI 变化。
- 测试：事件桥 token 日志、Pipeline 汇总。
