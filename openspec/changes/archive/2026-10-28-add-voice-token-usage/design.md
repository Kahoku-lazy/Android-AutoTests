## Context

`RealtimeAgent._finish_response()` 会发 `ModelCallEndEvent(reply_id, input_tokens, output_tokens, cache_*)`；`TranscriptBridge.handle()` 目前只处理 Reply/Text 事件。`ChatResponse.usage` 是 DeepSeek 标准用量对象。

## Decisions

1. Omni 在 `TranscriptBridge` 内累计并写 `model_usage`，`RealtimeVoiceSession` 从 bridge 读汇总写 `session_end`。
2. Pipeline 在 `DeepSeekAnswerer` 保存 `last_usage`，`_answer()` 完成后写 `model_usage` 并累计。
3. ASR `ResponseDoneEvent` 作为 `asr_usage` 记录；TTS 按字符计费，不在 token 口径内。
4. 只在 usage 字段存在且非零时写事件；`session_end` 始终带 0 值汇总，便于统计。

## Risks

- 工具调用会产生多次 `ModelCallEndEvent`，按次记录，汇总相加。
- Omni 的 usage 可能包含音频 token，字段仍按 input/output 原样记录。
