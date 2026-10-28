## ADDED Requirements

### Requirement: Pipeline LLM 的 RAG 增强

系统 SHALL 为 Pipeline 路线的 `deepseek-flash` 提供本地 RAG：读取配置的数据目录（默认 `D:\Govee\data\rag_data`），解析 `.md/.txt` 文件，切块、嵌入并写入本地索引。用户每轮语音提问后，系统 MUST 先用问题检索相关片段，命中时把片段作为上下文注入 DeepSeek；未命中时 MUST 保持原有直接回答。RAG 不可用或检索失败 MUST NOT 中断语音会话。

#### Scenario: 按资料回答

- **WHEN** 用户问“长按开关按键 3 秒会怎样？”
- **AND** `rag_data` 的按键需求文档包含该说明
- **THEN** 检索结果包含对应资料片段
- **AND** DeepSeek 的回答引用“进入网络待机模式”等资料内容
- **AND** 回答不是仅凭模型自由编造

#### Scenario: 资料未覆盖

- **WHEN** 用户问题在 `rag_data` 中没有相关片段
- **THEN** 系统不注入空上下文
- **AND** DeepSeek 仍正常回答或明确说不知道

#### Scenario: RAG 不可用降级

- **WHEN** 数据目录缺失、嵌入失败或索引损坏
- **THEN** 语音会话仍可建立
- **AND** 回答退化为无 RAG 的直接对话
- **AND** 失败原因写入运行期日志，不向前端泄露密钥

#### Scenario: 索引增量更新

- **WHEN** `rag_data` 中某个文件内容变化
- **THEN** 下一次检索前只重建该文件的文档
- **AND** 未变化文件不重复嵌入

#### Scenario: Omni 直连不注入

- **WHEN** 用户选择 `omni` 路线
- **THEN** 不经过 DeepSeek 文本 LLM
- **AND** 本期不注入 RAG 片段（需要时后续用工具调用扩展）
