## REMOVED Requirements

### Requirement: 本地知识检索由语音与文字共用

**Reason**: 本期先单独验收索引和检索，不让语音模型消费检索结果。
**Migration**: 语音会话暂时不挂载 `search_knowledge`。检索质量由知识库探针验收；确认后再另立变更恢复语音工具检索。

## ADDED Requirements

### Requirement: 语音会话本期不消费本地知识库

语音会话 MUST 在本期不挂载本地知识检索工具，也 MUST NOT 指示实时模型先检索再回答。缺少知识检索 MUST NOT 阻止语音会话建立。本地索引与检索 MUST 继续可由知识库探针独立执行。

#### Scenario: 语音会话没有检索工具

- **WHEN** 建立一个语音会话
- **THEN** 实时模型的工具列表不包含 `search_knowledge`
- **AND** 系统提示词不要求先检索本地资料

#### Scenario: 检索能力仍可独立验收

- **WHEN** 语音会话未挂载检索工具
- **THEN** 知识库探针仍可对指定库执行索引和检索
- **AND** 探针不创建语音会话
