# knowledge-base-retirement Specification

## Purpose

约定「知识库（RAG）」能力整体下线：不再有文档库入口、上传/检索页面、RAG 端点或向量库依赖，智能体也不再有知识库开关与引用范围字段；侧栏只允许与 AI 助手并列的「知识库助手」语音问答入口，该入口不得声称提供文档库能力。同时守住「任务附件能力不受影响」这条边界。

## Requirements

### Requirement: 知识库产品面已下线

RAG 知识库（文档上传、文档解析、引用范围、向量化与检索）MUST 保持下线：系统 MUST NOT 暴露 RAG 知识库入口、文档上传入口、引用范围配置或检索结果，也不得通过模型调试页展示知识库区块、知识库计数或知识库来源清单。侧栏「AI 功能」分组 MAY 提供「知识库助手」语音问答入口，但该入口 MUST NOT 声称提供文档知识库、文档上传、引用范围或 RAG 检索能力；该入口 MUST NOT 打开 `/ai-assistant/knowledge` 或任何已移除的知识库页面。

#### Scenario: 侧栏不再有知识库子项

- **WHEN** 已登录用户查看侧栏「AI 功能」分组
- **THEN** 子项只有「AI 助手」与「知识库助手」
- **AND** 不存在「知识库」「知识库文档」「引用范围」等 RAG 子项
- **AND** 「知识库助手」的入口文案与页面说明都不出现「文档库」「上传文档」「RAG」字样

#### Scenario: 知识库助手不是 RAG 页面

- **WHEN** 用户打开 `/knowledge-assistant`
- **THEN** 页面只提供语音按键与对话记录
- **AND** 页面不请求任何知识库文档、引用范围或检索接口

#### Scenario: 旧知识库路径仍然不可达

- **WHEN** 请求 `/ai-assistant/knowledge` 或任一已移除的 RAG 知识库端点
- **THEN** 不渲染知识库页面，且返回 404 或登录拦截

#### Scenario: 模型调试页不再出现知识库

- **WHEN** 超管打开任一角色调试子页
- **THEN** 角色带的计数与参考数据区都不出现「知识库」字样
- **AND** 页面不请求任何知识库接口

### Requirement: 知识库 HTTP 面已下线

系统 MUST NOT 暴露知识库相关端点；对已移除路径的请求 MUST 返回 404。平台配置的读取与写入 MUST NOT 再包含知识库开关与引用范围字段。

#### Scenario: 旧端点不再可用

- **WHEN** 请求 `/api/ai/knowledge/status/`、`/api/ai/knowledge/documents/`、`/api/ai/knowledge/documents/preview/`、`/api/ai/knowledge/reindex/` 或 `/api/ai/knowledge/documents/add/`
- **THEN** 均返回 404

#### Scenario: 平台配置不再含知识库字段

- **WHEN** 读取平台配置或提交平台配置更新
- **THEN** 响应与入参都不含 `enable_knowledge_base` 与 `knowledge_sources`

### Requirement: 知识库实现与数据面已移除

系统 MUST NOT 保留 RAG 服务实现、知识库视图模块、向量库依赖与知识库专用代码路径。智能体记录 MUST NOT 保留知识库开关与引用范围字段。

#### Scenario: 无知识库实现残留

- **WHEN** 检索后端代码与依赖声明
- **THEN** 不存在 RAG 服务模块、知识库视图模块，也不再声明 chromadb 依赖

#### Scenario: 智能体记录不再有知识库字段

- **WHEN** 检查智能体表结构与智能体详情响应
- **THEN** 不存在 `enable_knowledge_base` 与 `knowledge_sources`

### Requirement: 任务附件能力不受影响

删除知识库 MUST NOT 改变任务附件的上传、解析与展示行为。

#### Scenario: 任务附件照常解析

- **WHEN** 用户提交带 docx 或 pdf 附件的任务
- **THEN** 附件仍被解析为 Markdown 并随规划模型输入下发，与删除知识库前一致
- **AND** 不支持的后缀仍被拒绝并给出可读错误
