## 1. Omni

- [x] 1.1 `events.py` 处理 `ModelCallEndEvent`，写 `model_usage` 并累计
- [x] 1.2 `session.py` 在 `session_end` 带 token 汇总

## 2. Pipeline

- [x] 2.1 `pipeline_llm.py` 保存 DeepSeek `ChatResponse.usage`
- [x] 2.2 `pipeline.py` 写 `model_usage` / `asr_usage`，`session_end` 带汇总

## 3. 验证

- [x] 3.1 事件桥单测断言 token 日志与汇总
- [x] 3.2 Pipeline 单测断言 `last_usage`
- [x] 3.3 ruff / pytest
- [x] 3.4 `openspec validate add-voice-token-usage --strict` 并归档
