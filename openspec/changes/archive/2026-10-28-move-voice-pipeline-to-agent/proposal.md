## Why

语音助手的 `pipeline` 路线（ASR → DeepSeek → TTS）里，回答是与模型直连、语音是另起一次合成：`DeepSeekAnswerer` 自己拼消息、自己算增量，`SambertTts` 在全文结束后整段合成。这条链路因此拿不到引擎侧的任何护栏——**预算、重试、追踪、RAG 中间件全都用不上**，语音助手成了中间件体系之外的孤岛。

上一步已经把「模型重试 / 预算 / RAG / 语音合成」都做成了可装配的中间件；本变更把 pipeline 的**回答与语音合成**接到这套体系上，ASR 与传输层不动。

## What Changes

- 新增 `engines/agents/realtime_vocie/tts_model.py`：`LocalTtsModel(TTSModelBase)` 把现有 `SambertTts` / `QwenTts` 适配成框架 TTS 模型——**音色与 provider 都不变**，只是换一层接口。
- 新增 `engines/agents/realtime_vocie/agent_answerer.py`：`AgentAnswerer` 用 `Agent` 跑一轮回答，`TextBlockDeltaEvent` → 文本增量，`DataBlockDeltaEvent` → 解码攒音频，`ModelCallEndEvent` → token 用量。
- `PipelineVoiceSession`：新增 `_create_agent_answerer()`，装配 `build_agent_middlewares(with_tts=False, extra=[RagContextMiddleware?, TTSMiddleware(LocalTtsModel)])`；`_answer` 在 Agent 模式下用 `answerer.take_audio()` 取代 `self._tts.synthesize(full)`。
- 配置：`KNOWLEDGE_ASSISTANT_PIPELINE_ENGINE`（`agent` 默认 / `legacy` 回退），非法值拒绝启动并给出可读原因。
- **音频仍整段发**：中间件逐块吐音频，但由回答器攒成一段 PCM，在 `reply_end` 前一次 `send_audio` —— 前端帧格式零改动。
- **计费口径不变**：`model_usage` 取 `ModelCallEndEvent` 的四个 token 字段；`tts_usage` 仍按本轮总字符数记一条。

## 关联文档

- `openspec/specs/knowledge-assistant-voice/spec.md`：新增「Pipeline 回答链路可由 Agent 承担」的要求。
- `openspec/specs/agent-middleware-assembly/spec.md`：装配入口新增 `with_tts` / `extra` 两个参数（供语音链路自带 TTS）。
- `engines/agents/realtime_vocie/AGENTS.md`：事件契约与「不反向依赖后端」红线继续适用。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-assistant-voice`：pipeline 回答链路改由 Agent + 中间件承担，并保留 `legacy` 回退。

## Impact

- 新增：`engines/agents/realtime_vocie/{tts_model,agent_answerer}.py`、`tests/graybox/unit/test_voice_agent_answerer.py`
- 修改：`engines/agents/realtime_vocie/{config,pipeline}.py`、`engines/agents/middleware/assembly.py`
- 需要真机验收：语音链路无法用单测覆盖音质与实时性，单测只覆盖事件映射、音频拼接、配置开关
- 不影响：ASR 接入、前端事件帧、omni / livetranslate 两条路线
