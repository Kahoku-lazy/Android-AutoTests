## Context

`PipelineVoiceSession` 只依赖 TTS 的 `synthesize(text) -> pcm_bytes` 与 `sample_rate`。Qwen-TTS 是 HTTP 非流式；Sambert 是 WebSocket `run-task` 协议，两者可以在同一接口下互换。

## Goals / Non-Goals

**Goals:**

- Pipeline 默认使用 `sambert-zhichu-v1`，中文播报可用。
- Qwen-TTS 保留为可选，便于对比音质/价格。
- 不改前端结构，ready 事件自动反映模型与音色。

**Non-Goals:**

- 不做 Sambert 流式边生成边播（Sambert 本身就是整段文本 `streaming: out`）。
- 不做英文 Eva 音色自动切换；需要英文时用配置改 `sambert-eva-v1`。
- 不把 Sambert 用于 ASR/LLM。

## Decisions

### 1. 新增 SambertTts，而不是修改 QwenTts

两个类都实现 `synthesize(text)` 与 `sample_rate`；`pipeline.py` 按 provider 选类。QwenTts 保持现状，避免回归。

### 2. Sambert 走标准域名

当前 Key 实测可连 `wss://dashscope.aliyuncs.com/api-ws/v1/inference`，无需 WorkspaceId。连接头带 Bearer Key；`run-task` 的 `format=pcm`、`sample_rate=24000`，二进制帧直接拼接为 PCM16。

### 3. 默认知厨，Eva 只作为英文可选

`sambert-zhichu-v1` 是中文音色；`sambert-eva-v1` 是英文音色。默认用知厨，避免中文回答被英文音色读成怪音。配置可改 `KNOWLEDGE_ASSISTANT_PIPELINE_TTS_MODEL`。

### 4. provider 配置

`KNOWLEDGE_ASSISTANT_PIPELINE_TTS_PROVIDER=sambert|qwen`，默认 `sambert`。`config.py` 根据 provider 给默认 model/voice；显式 env 优先。

## 模块防火墙自检

- TTS 适配器在引擎层，只依赖标准库、httpx/websockets；不 import 后端。
- 前端只展示 ready 的 model/voice，不直连 Sambert。
- 无数据库、无新 WS 通道。

## Risks / Trade-offs

- [Sambert 音质较机械] → 保留 Qwen-TTS 可选；用户可切回。
- [Sambert 需要整段文本] → 先出文字再合成，首包延迟约 1–2 秒。
- [中文/英文音色混用] → 默认知厨；英文场景显式改 Eva。
- [长文本] → 复用 `_split_text` 分段合成并拼接 PCM。
