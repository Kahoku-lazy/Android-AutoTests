## REMOVED Requirements

### Requirement: Pipeline LLM 的 RAG 增强
**Reason**: RAG 不再只服务 Pipeline；Omni 也需要通过工具调用使用同一份本地资料。
**Migration**: 由新增的「语音 LLM 的 RAG 增强」统一覆盖 Pipeline 注入与 Omni 工具调用。

## ADDED Requirements

### Requirement: 语音 LLM 的 RAG 增强

系统 SHALL 为语音助手提供本地 RAG：读取配置的数据目录（默认 `D:\Govee\data\rag_data`），解析 `.md/.txt`，切块、嵌入并写入本地索引。

- `pipeline`：每轮提问后先检索，命中片段作为上下文注入 `deepseek-flash`。
- `omni`：通过 `search_knowledge` 只读工具检索，把工具结果交回实时模型组织回答。

未命中时 MUST 保持原有直接回答；RAG 不可用或检索失败 MUST NOT 中断语音会话。

#### Scenario: Pipeline 按资料回答

- **WHEN** 用户问“长按开关按键 3 秒会怎样？”
- **AND** `rag_data` 的按键需求文档包含该说明
- **THEN** 检索结果包含对应资料片段
- **AND** DeepSeek 的回答引用“进入网络待机模式”等资料内容

#### Scenario: Omni 通过工具检索

- **WHEN** 用户选择 `omni` 路线并问 H717D 按键问题
- **THEN** 实时模型可调用 `search_knowledge` 工具
- **AND** 工具返回本地资料片段
- **AND** 助手语音回答基于工具结果，而不是仅凭模型记忆

#### Scenario: 资料未覆盖

- **WHEN** 用户问题在 `rag_data` 中没有相关片段
- **THEN** 系统不注入空上下文或工具返回“没有相关资料”
- **AND** 助手仍正常回答或明确说不知道

#### Scenario: RAG 不可用降级

- **WHEN** 数据目录缺失、嵌入失败或索引损坏
- **THEN** 语音会话仍可建立
- **AND** 回答退化为无 RAG 的直接对话
- **AND** 失败原因写入运行期日志，不向前端泄露密钥

#### Scenario: 索引增量更新

- **WHEN** `rag_data` 中某个文件内容变化
- **THEN** 下一次检索前只重建该文件的文档
- **AND** 未变化文件不重复嵌入
