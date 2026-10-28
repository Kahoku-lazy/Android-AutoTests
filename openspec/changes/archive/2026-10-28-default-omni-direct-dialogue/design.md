## Context

参考 `temps/realtime_voice_demo`：`RealtimeAgent` + `DashScopeRealtimeModel` + 一句简短中文系统提示，用户说话后模型自由回答，没有平台知识注入。当前 `knowledge.py` 注入了平台模块速览和“回答约束”，容易让回复看起来像预设脚本；默认还停在 livetranslate，导致页面打开后只翻译。

## Goals / Non-Goals

**Goals:**

- 默认 omni，打开就是问答；livetranslate 仍可显式选择。
- 系统提示词收敛为直接对话，不注入预设答案。
- 保持现有 WS、音频、转写、日志与 UI 结构。

**Non-Goals:**

- 不接入 RAG/知识库检索；本期是自由对话。
- 不改翻译适配器；它仍是可选模式。
- 不改前端布局。

## Decisions

### 1. 默认 omni

`DEFAULT_MODE=omni`、`DEFAULT_MODEL=qwen3.5-omni-plus-realtime`。`livetranslate` 通过 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=livetranslate` 或模型名自动推断启用。这样“核心问答”开箱即用，翻译作为降本选项。

### 2. 提示词参考 Demo，只保留直接对话约束

`knowledge.py` 改为：
```
你是一个中文语音助手，正在通过语音和用户直接对话。
回答尽量简短、口语化，通常不超过三句话。
```
不注入平台模块清单、固定答案或“必须先说某模块”的规则。模型可自由回答；不知道时自然说不知道。

### 3. 不新增预设回复层

`TranscriptBridge`、session、前端都不做关键词→固定回复的映射；回复完全来自模型 `TranscriptDeltaEvent`。单测通过检查提示词不含平台速览来守住这一点。

## 模块防火墙自检

- 只改引擎配置与提示词；后端 consumer/runtime/日志不变。
- 引擎仍不 import 后端 App；前端只展示 mode。
- 无数据库、无新 WS 通道。

## Risks / Trade-offs

- [没有平台知识，模型可能答得不准确] → 这是“直接对话”的取舍；后续可通过知识库检索或工具增强，而不是塞预设答案。
- [默认 omni 费用高于 livetranslate] → 需要降本时显式切 livetranslate；页面会显示「实时翻译」。
- [旧 `.env` 仍写 livetranslate] → 本地 `.env` 已切 omni；`.env.example` 默认 omni 并给翻译示例。
