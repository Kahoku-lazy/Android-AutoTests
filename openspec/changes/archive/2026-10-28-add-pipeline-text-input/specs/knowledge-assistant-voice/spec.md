## ADDED Requirements

### Requirement: Pipeline 文本输入

`pipeline` 路线 SHALL 提供文本输入框；用户输入文字后，系统 MUST 跳过 ASR，把文字直接交给 DeepSeek（含 RAG）并合成 TTS 音频。未开始会话时发送文字 MUST 自动建立纯文本会话：不申请麦克风、不发送空音频，但仍建立播放器与 `/ws/knowledge-assistant/?mode=pipeline` 连接。

WS 客户端消息白名单 SHALL 在 `interrupt` / `played` 之外增加 `text`，且 `text` 只允许 Pipeline 会话处理。

#### Scenario: 纯文本提问

- **WHEN** 用户在 Pipeline 路线输入“长按开关按键3秒会怎样？”并发送
- **THEN** 页面出现用户文本消息
- **AND** DeepSeek 按 RAG 资料生成回答
- **AND** 浏览器播放 Sambert TTS 音频

#### Scenario: 会话中追加文字

- **WHEN** 语音会话已开始，用户输入文字并发送
- **THEN** 当前回答被取消（如有）
- **AND** 新文字作为新一轮用户问题处理

#### Scenario: 纯文本不打麦克风提示

- **WHEN** 用户未授权麦克风、仅使用文字提问
- **THEN** 会话正常建立
- **AND** 不显示“没有检测到麦克风音频”的提示

#### Scenario: Omni 路线不显示文本输入

- **WHEN** 路线为 `omni`
- **THEN** 不显示 Pipeline 文本输入框
