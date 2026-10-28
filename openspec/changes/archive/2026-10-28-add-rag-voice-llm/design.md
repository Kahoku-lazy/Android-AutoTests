## Context

`rag_data` 当前是 4 个 Markdown 产品资料（按键、指示灯、工厂状态、固件需求）。Pipeline 的 DeepSeek 是标准 ChatModel，可在每轮 user message 前插入检索上下文。AgentScope 2.0.10 提供 `TextParser`、`ApproxTokenChunker`、`DashScopeEmbeddingModel`、`KnowledgeBase` 和 `VectorStoreBase`；本机已安装 `agentscope` 与 `numpy`，没有 Qdrant/Milvus 客户端。

## Goals / Non-Goals

**Goals:**

- 数据目录 → 本地索引 → 检索 → DeepSeek 上下文，一条可验证链路。
- 索引落盘、按文件增量更新，服务重启不重复嵌入。
- 不新增外部数据库/服务，不阻塞语音会话。

**Non-Goals:**

- 不做文档上传 UI、权限、多租户。
- 不做 Omni 实时模型的工具调用 RAG（本期只接 Pipeline DeepSeek）。
- 不做 rerank/混合检索；先用向量 top-k。

## Decisions

### 1. 用 AgentScope 组件 + 自定义 SQLite 向量库

- 解析：`TextParser`（Markdown 整文件 Section）。
- 切块：`ApproxTokenChunker(chunk_size=400, overlap=60)`。
- 嵌入：`DashScopeEmbeddingModel` + `text-embedding-v4`（1024 维）。
- 知识库：`KnowledgeBase` 绑定 `SQLiteVectorStore`。
- 选择 SQLite 而不是 Qdrant/Milvus：当前环境无对应客户端，4 个文档规模很小；SQLite 无新依赖、可持久化、易测试。`SQLiteVectorStore` 实现 `VectorStoreBase` 的 create/delete/has/insert/delete/search/list_documents。

### 2. 索引目录与增量

- 默认数据目录 `D:\Govee\data\rag_data`；索引目录 `data/rag_index/rag.sqlite3`，状态 `index_state.json`。
- 文档 ID 由相对路径 SHA1 生成；文件 mtime/size 变化时删除旧 document 再插入；删除的文件从索引移除。
- `RagService.ensure_index()` 用 `asyncio.Lock` 防止并发重复建索引。

### 3. 每轮检索注入，不写进历史

`DeepSeekAnswerer.stream(text)`：
1. `RagService.build_context(text)` 检索 top_k。
2. 有命中时把 `【检索资料】...` 放在本轮 user 内容前，并追加系统约束“优先依据资料，资料没有的不要编造”。
3. 历史仍只保存原始用户问题与助手回答，避免上下文膨胀。

### 4. 失败降级

`RagService` 初始化/索引/检索异常只记录日志并返回空上下文；Pipeline 不因 RAG 失败而中断。状态接口可展示 `rag_enabled`，但不暴露路径细节。

## 模块防火墙自检

- 所有 AgentScope RAG/索引/检索代码在 `engines/agents/rag/`；realtime_vocie 只 import `RagService`。
- 不 import 后端 App；不写数据库模型；索引是本地文件。
- 前端只展示回答文本，不需要新组件。

## Risks / Trade-offs

- [首次索引延迟] → 4 个文档约数十个 chunk；首次会话多 1–2 秒，之后走缓存。
- [向量检索召回不准] → top_k/阈值可配；后续可加 rerank/关键词混合。
- [SQLite 不适合大规模] → 当前数据量小；规模上来再换 Qdrant/Milvus。
- [Omni 无 RAG] → 明确只在 Pipeline 生效；需要时再给 Omni 加工具。
