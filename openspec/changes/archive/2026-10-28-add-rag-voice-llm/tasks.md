## 1. RAG 引擎

- [x] 1.1 新增 `engines/agents/rag/config.py`：数据目录、索引目录、嵌入模型、top_k/阈值
- [x] 1.2 新增 `engines/agents/rag/store.py`：`SQLiteVectorStore` 实现 `VectorStoreBase`
- [x] 1.3 新增 `engines/agents/rag/indexer.py`：TextParser + ApproxTokenChunker + KnowledgeBase，按文件增量重建
- [x] 1.4 新增 `engines/agents/rag/service.py`：`RagService.search/build_context`，失败降级
- [x] 1.5 新增 `engines/agents/rag/AGENTS.md` 与 `__init__.py`

## 2. 接入 Pipeline

- [x] 2.1 `DeepSeekAnswerer` 接收 `RagService`，每轮注入检索上下文
- [x] 2.2 `PipelineVoiceSession` 创建 RAG 服务并确保索引；失败不阻塞
- [x] 2.3 `.env.example` 增加 RAG 配置

## 3. 验证

- [x] 3.1 对 `D:\Govee\data\rag_data` 建索引，查询“长按开关按键 3 秒”命中按键文档
- [x] 3.2 DeepSeek 的 RAG 回答包含资料内容；无命中问题正常回答
- [x] 3.3 Pipeline 真实 WAV 仍跑通，RAG 失败时可降级
- [x] 3.4 ruff / pytest / `manage.py check` / 前端 typecheck
- [x] 3.5 `openspec validate add-rag-voice-llm --strict` 并归档
