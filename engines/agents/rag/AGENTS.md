# rag 模块 AGENTS.md

> 二级约束：根 `AGENTS.md`、`engines/AGENTS.md`、`engines/agents/AGENTS.md` 优先。

## 职责

为语音助手提供本地 RAG：Pipeline 把检索上下文注入 DeepSeek；Omni 通过 `search_knowledge` 工具调用同一套索引。

| 文件 | 职责 |
| --- | --- |
| `config.py` | 数据目录、索引目录、嵌入模型、切块/检索参数 |
| `store.py` | `SQLiteVectorStore`：AgentScope `VectorStoreBase` 的本地实现 |
| `chunker.py` | `MarkdownHeadingChunker`：按 `##+` 标题切块，过大段回退近似 token |
| `indexer.py` | `TextParser` + `MarkdownHeadingChunker` + `KnowledgeBase`，按文件/切块版本增量重建 |
| `service.py` | `RagService.search/build_context`，失败降级 |
| `tool.py` | `build_rag_tool()`：Omni 的只读 `search_knowledge` 工具 |

## 红线

1. **只读资料目录**：`D:\Govee\data\rag_data` 只读；索引只写 `data/rag_index/`。
2. **不反向依赖**：禁止 import `backend.apps.*`；日志用 `utils.logs`。
3. **不泄露密钥**：`EMBEDDING_API_KEY` / `DASHSCOPE_API_KEY` 不写日志、不进上下文。
4. **失败降级**：索引/检索失败只返回空上下文，不能中断语音会话。
5. **文本-only**：当前只索引 `.md/.txt`；多模态资料不进入 SQLite 向量库。
6. **不把 RAG 结果写进长期历史**：只注入当轮 user 上下文，历史保存原始问题。

## 快速验证

```powershell
python -c "from engines.agents.rag import RagService; print(RagService.from_env())"
ruff check engines/agents/rag
python -m pytest -c tests/pytest.ini tests/graybox/unit/test_rag_*.py -q
```

