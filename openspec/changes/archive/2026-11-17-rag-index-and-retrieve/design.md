## Context

`engines/agents/rag` 已有切块、SQLite 向量库、增量索引和检索服务，但文字会话与语音会话各自创建服务并挂载 `search_knowledge`。检索结果因此只能通过模型回答间接观察。行为要求见本变更的 delta specs。

约束：

- 只使用嵌入模型，模型实例仍经 `engines.agents.models` 门面创建。
- 不恢复已下线的知识库 HTTP 接口和上传页面。
- `load_log_keywords(sku)` 继续整篇直读，不被向量检索替代。
- 引擎不依赖 Django 或后端 App。

## Goals / Non-Goals

**Goals:**

- 用库表描述多个物理隔离的知识库。
- 对指定库增量建索引，并返回未经改写的命中。
- 提供不创建智能体的命令行探针。
- 从文字会话、语音会话和中间件装配中摘掉本期的知识库消费。

**Non-Goals:**

- 不实现角色授权和工具挂载。
- 不把 `log_keywords` 库启用为向量库。
- 不替换 SQLite，不引入 Qdrant、Redis 或 RAG 服务。
- 不调用聊天模型判断检索是否正确。

## Decisions

### 1. 库表独立于角色表和模型表

新增 `engines/agents/config/data/knowledge_bases.yaml`。库名、说明、资料目录和启用状态放在这里。角色表本期不增加 `knowledge_bases` 字段，避免配置显示已接入但运行时没有工具。

备选是继续使用单一 `KNOWLEDGE_ASSISTANT_RAG_DATA_DIR`。它无法表达多库隔离，因此不保留为索引范围的主配置。总开关、嵌入模型、切块和检索阈值仍由环境变量覆盖。

### 2. 一个库对应一个 collection 和一份增量状态

启用库使用同名 SQLite collection，增量状态写到 `data/rag_index/collections/<库名>/index_state.json`。不使用 metadata 把多个库塞进同一个 collection，避免过滤遗漏造成跨库命中。

### 3. 检索只接受一个库名

`retrieve(base, query)` 不提供默认的全库搜索。调用方必须点名库。结果使用结构化命中，字段为库名、来源、文档编号、片段序号、相似度和正文。`format_context()` 不再作为检索主返回值，因为它把多条命中拼成提示词，不适合验收切块。

### 4. 失败分层

库表损坏、库名非法和嵌入配置缺失属于调用错误，探针返回非零退出码。资料目录缺失、嵌入请求失败和无命中属于该库的检索结果，返回空列表与可读原因，不抛给调用方。一次失败不得永久缓存成「已就绪」，下次调用允许重试。

### 5. 向量库补齐异步上下文

`SQLiteVectorStore` 实现 `__aenter__` / `__aexit__`。当前没有长连接，两个方法可以为空，但索引和检索都用 `async with` 调用。这样满足 AgentScope 2.0.9 的向量库生命周期契约，以后替换有连接的向量库时不用改调用方。

### 6. 智能体侧只摘引用，不改回答模型

文字会话仍用 `deepseek-flash`，语音会话仍用 Omni。两者都不再创建 RAG 服务、不再挂载检索工具。语音会话同时去掉「先调用 `search_knowledge`」的附加提示。`build_agent_middlewares()` 不再装配 `RagContextMiddleware`，因为该中间件把命中长期追加到系统提示词，和本期验收目标相反。

### 7. 探针作为唯一人工验收口

`python -m engines.agents.rag index <库名>` 和 `python -m engines.agents.rag retrieve <库名> <问题>` 是本期验收入口。探针只调用嵌入模型。没有命中时退出码为 0，配置或参数错误时退出码为 1。

## 模块防火墙自检

- 不新增跨 App import。RAG 仍在 `engines/agents/rag`，后端不新增知识库接口。
- 不写业务数据库，不新增 `INSERT` / `UPDATE` / `DELETE`。本地索引文件不属于业务库。
- 前端不连接向量库，不新增页面。
- 引擎仍不 import `django` 或 `backend.apps`。
- 嵌入模型只经 `engines.agents.models` 门面获取，不在 RAG 内构造模型类。

## Risks / Trade-offs

- [知识库助手暂时不能依据资料回答] → 这是本期预期。探针先证明命中正确，后续变更再接回工具。
- [旧索引 collection 名称与新库名不同] → 新库使用新 collection，不迁移旧 `voice_knowledge` 数据；首次索引会重新嵌入。
- [SQLite 全表余弦扫描随资料增长变慢] → 本期资料规模小，先保持本地实现；库边界已经按 collection 分开，后续可替换向量库。
- [0.55 阈值只适用于余弦相似度] → 配置和探针都把它标成当前度量的过滤线，不解释为准确率。

## Migration Plan

1. 增加库表，只启用 `product_manuals`。
2. 将索引和检索改为按库执行，并补探针。
3. 摘掉文字、语音和中间件的检索消费。
4. 用临时资料目录运行探针；确认命中后再考虑接回智能体。
5. 回退时恢复两个会话的工具挂载，并保留新库表不启用即可停止新索引行为。

## Open Questions

无。角色授权、工具挂载和 `log_keywords` 向量化都明确留到后续变更。
