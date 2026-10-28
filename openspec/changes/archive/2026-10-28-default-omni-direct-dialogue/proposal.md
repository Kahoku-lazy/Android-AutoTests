## Why

知识库助手的核心是「我问模型答」的直接对话，而 `qwen3.8-livetranslate-flash-realtime` 只做翻译、不会回答问题。上一轮为了降本把它设为默认，导致页面打开后不是问答。现在改为默认 `qwen3.5-omni-plus-realtime` 直接对话，并把系统提示词收敛成参考 Demo 的简洁助手提示，不再注入平台知识速览或预设答案。

## What Changes

- 默认调用方式改为 `omni`，默认模型 `qwen3.5-omni-plus-realtime`；`livetranslate` 保留为可选的低成本翻译模式。
- 移除 `knowledge.py` 里的平台模块速览与回答约束，只保留「中文语音助手、简短口语化、不超过三句话」的直接对话提示。
- 明确助手回复由模型自由生成，不匹配预设答案、不注入固定话术。
- 前端「模式」行仍显示「语音问答」/「实时翻译」；默认显示语音问答。
- 本地 `.env` 已切到 omni，用于问答验收。

## 关联文档

- `temps/realtime_voice_demo` 的直接对话实现（`RealtimeAgent` + 简短中文系统提示）
- 已归档变更 `2026-10-28-add-knowledge-assistant-voice`、`2026-10-28-switch-realtime-model-to-livetranslate`

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 默认调用方式从 livetranslate 改为 omni；新增「直接对话不注入预设答案」需求。

## Impact

- 引擎：`config.py` 默认 mode/model；`knowledge.py` 提示词；`create_realtime_model` 默认走 Omni。
- 前端：无需结构改动，默认模式文案随状态变为「语音问答」。
- 配置：`.env.example` 默认 omni，并保留 livetranslate 可选示例。
- 测试：默认配置/状态断言更新；提示词单测改为验证无平台预设答案。
