## Why

当前 RAG 把建索引、检索和智能体回答绑在一起，无法单独判断切块、相似度和命中正文是否正确。需要先把知识库收成只使用嵌入模型的索引与检索模块，并用原始命中验收，再决定是否接回智能体。

## What Changes

- 新增按库名隔离的本地知识库目录、增量索引和原始检索结果。
- 新增只打印来源、片段号、相似度和正文的命令行探针，不调用聊天模型或语音模型。
- **BREAKING** 文字会话和语音会话本期不再挂载 `search_knowledge`，知识库助手暂时退回普通对话。
- **BREAKING** 移除把检索片段追加到系统提示词的 RAG 中间件装配。
- 不恢复文档上传页面和已下线的 `/api/ai/knowledge/*`。

## 关联文档

PRD-08。知识库助手本期只保留问答入口，不对用户开放 RAG 文档库运营；本次只建设 engines 内的索引与检索能力。

## Capabilities

### New Capabilities

- `knowledge-index-and-retrieve`: 多库目录、增量索引、按库检索和命令行探针

### Modified Capabilities

- `knowledge-assistant-voice`: 暂停语音与文字共用 `search_knowledge` 的要求
- `knowledge-assistant-text-chat`: 暂停文字会话必须依据本地检索回答的要求
- `agent-middleware-assembly`: 移除把检索结果注入系统提示词的中间件要求

## Impact

- 引擎：`engines/agents/rag`、`engines/agents/knowledge_chat`、`engines/agents/realtime_vocie`、`engines/agents/middleware`
- 配置：新增 `engines/agents/config/data/knowledge_bases.yaml`
- 测试：`tests/engines/agents/unit/` 下的 RAG、文字会话、语音会话和中间件装配测试
- 不新增后端接口，不改前端页面
