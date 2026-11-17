## MODIFIED Requirements

### Requirement: 文字会话使用 DeepSeek Flash 与本地知识检索

文字会话 MUST 使用 `deepseek-flash` 作为回答模型。本期 MUST NOT 挂载本地知识检索工具，也 MUST NOT 把检索片段注入回答上下文。回答 MUST NOT 来自预设答案表。缺少本地检索 MUST NOT 中断文字会话。

#### Scenario: 本期不挂载检索工具

- **WHEN** 建立一个文字会话
- **THEN** 回答模型是 `deepseek-flash`
- **AND** 工具列表不包含 `search_knowledge`

#### Scenario: 不依据检索片段回答

- **WHEN** 用户提出产品资料问题
- **THEN** 文字会话直接把问题交给回答模型
- **AND** 不读取或注入本地知识库命中

#### Scenario: 检索模块独立可用

- **WHEN** 文字会话没有挂载检索工具
- **THEN** 知识库探针仍可独立检索指定库
- **AND** 探针结果不进入文字会话上下文
