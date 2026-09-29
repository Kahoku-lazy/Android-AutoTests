# knowledge-base-retirement Specification

## Purpose

约定「知识库（RAG）」能力整体下线：产品面不再有入口与页面，HTTP 面不再有端点，智能体不再有知识库开关与引用范围字段，实现面不再有 RAG 服务与向量库依赖，从而消除残留的可调用能力、误导性的界面承诺与随之而来的权限缺口；同时守住「任务附件能力不受影响」这条边界。

## Requirements

### Requirement: 知识库产品面已下线

系统 MUST NOT 在 AI 助手侧栏、路由表或页面中暴露知识库入口。访问已移除路径 MUST NOT 渲染知识库页面。模型调试页 MUST NOT 展示知识库区块、知识库计数或知识库来源清单。

#### Scenario: 侧栏不再有知识库子项

- **WHEN** 已登录用户查看侧栏「AI 助手」分组
- **THEN** 子项中不含「知识库」
- **AND** 前端路由表中不存在 `/ai-assistant/knowledge`

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
