## REMOVED Requirements

### Requirement: 调用方式可选且默认实时翻译模型
**Reason**: 实时翻译模型只翻译、不回答问题，与知识库助手「我问模型答」的核心不符；默认改为 Omni 直接对话。
**Migration**: 使用 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=livetranslate` 显式启用翻译模式；不配置时默认 `omni`。

## ADDED Requirements

### Requirement: 调用方式可选且默认 Omni 直接对话

系统 SHALL 支持两种实时语音调用方式：`omni`（实时对话）与 `livetranslate`（实时翻译）。默认调用方式 MUST 为 `omni`，默认模型 MUST 为 `qwen3.5-omni-plus-realtime`。用户 SHALL 能通过环境变量 `KNOWLEDGE_ASSISTANT_REALTIME_MODE` 显式选择调用方式，或仅设置 `KNOWLEDGE_ASSISTANT_MODEL` 由模型名推断：包含 `livetranslate` 走翻译，否则走 `omni`。调用方式与模型名不匹配时，系统 MUST 拒绝启动并在状态接口返回可读原因。

#### Scenario: 默认使用 omni 问答

- **WHEN** 只配置 `DASHSCOPE_API_KEY`
- **THEN** 状态接口返回 `mode=omni`
- **AND** 模型为 `qwen3.5-omni-plus-realtime`

#### Scenario: 显式启用实时翻译

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=livetranslate` 与 `KNOWLEDGE_ASSISTANT_MODEL=qwen3.8-livetranslate-flash-realtime`
- **THEN** 会话使用实时翻译适配器

#### Scenario: 只配模型名自动推断

- **WHEN** 只配置 `KNOWLEDGE_ASSISTANT_MODEL=qwen3.8-livetranslate-flash-realtime`
- **THEN** 调用方式自动推断为 `livetranslate`

#### Scenario: 模式与模型不匹配

- **WHEN** 配置 `KNOWLEDGE_ASSISTANT_REALTIME_MODE=omni` 且模型为 LiveTranslate
- **THEN** 状态接口返回 `ready=false` 与可读原因
- **AND** 不创建模型会话

### Requirement: 直接对话不注入预设答案

系统 SHALL 使用简洁的直接对话系统提示词，MUST NOT 注入平台模块速览、固定答案话术或预先写好的回复。助手回复 MUST 由所选实时模型根据用户语音与通用中文语音助手提示自然生成，而不是从预设答案表中匹配。

#### Scenario: 用户自由提问

- **WHEN** 用户问一个平台使用问题
- **THEN** 助手回答由模型实时生成
- **AND** 代码中不存在按问题匹配的预设回复表

#### Scenario: 提示词只保留直接对话约束

- **WHEN** 检查知识库助手的系统提示词
- **THEN** 只包含中文语音助手角色、简短口语化、回答长度等通用约束
- **AND** 不包含「设备管理：扫描、连接……」这类平台知识速览或逐条回答模板
