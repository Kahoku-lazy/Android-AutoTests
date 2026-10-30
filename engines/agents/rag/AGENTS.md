# rag 模块 AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/agents/AGENTS.md`](../AGENTS.md) → **本文件**。本文件只写 RAG 领域增量；**冲突时本文件的领域规则优先**。  
> 风格正文与检查技能仍以上层「AI 阅读与检查流程」为准。

## 职责

为语音助手提供本地 RAG：Pipeline 把检索上下文注入 DeepSeek；Omni 通过 `search_knowledge` 工具调用同一套索引。

| 文件 | 职责 |
| --- | --- |
| `config.py` | 数据目录、索引目录、嵌入模型、切块/检索参数（路径以配置/环境变量为准） |
| `store.py` | `SQLiteVectorStore`：AgentScope `VectorStoreBase` 的本地实现 |
| `chunker.py` | `MarkdownHeadingChunker`：按 `##+` 标题切块，过大段回退近似 token |
| `indexer.py` | `TextParser` + `MarkdownHeadingChunker` + `KnowledgeBase`，按文件/切块版本增量重建 |
| `service.py` | `RagService.search/build_context`，失败降级 |
| `tool.py` | `build_rag_tool()`：Omni 的只读 `search_knowledge` 工具 |

## 红线（禁止）

1. **只读资料目录**：资料目录只读（常见本地路径示例 `D:\Govee\data\rag_data`，**以 `config` / 环境变量为准**）；索引只写 `data/rag_index/`（或配置中的索引目录）。
2. **不反向依赖**：禁止 `import apps.*` / `django.*` / `backend.apps.*`；日志用 `utils.logs`。
3. **不泄露密钥**：`EMBEDDING_API_KEY` / `DASHSCOPE_API_KEY` 不写日志、不进上下文。
4. **失败降级**：索引/检索失败只返回空上下文，不能中断语音会话。
5. **文本-only**：当前只索引 `.md/.txt`；多模态资料不进入 SQLite 向量库。
6. **不把 RAG 结果写进长期历史**：只注入当轮 user 上下文，历史保存原始问题。

## AI 阅读与检查流程（必读）

1. **任何 engines 任务**：先读 [`engines/AGENTS.md`](../../AGENTS.md)。
2. **改 RAG 目录职责、检索/索引行为、工具边界时**：再读**本文件**；必要时对照 [`engines/agents/AGENTS.md`](../AGENTS.md)。
3. **即将编写或修改本包代码时**：按上层流程先读 [`.agents/rules/engines-code-style.md`](../../../.agents/rules/engines-code-style.md)；禁止未读规范就写代码。
4. **只读分析 / 解释 / 排障且不改代码**：可以不读 style rules。
5. **需要自动化风格检查时**：使用 [`.agents/skills/engines-agents-style-check/`](../../../.agents/skills/engines-agents-style-check/)（`cd` 到技能目录后 `python -m scripts.check_engines_agents_style`）。过检 ≠ 整份规范合规。

## 快速验证

```powershell
python -c "from engines.agents.rag import RagService; print(RagService.from_env())"
ruff check engines/agents/rag
python -m pytest -c tests/pytest.ini tests/graybox/unit/test_rag_*.py -q
```

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层 engines 入口 | [`engines/AGENTS.md`](../../AGENTS.md) |
| agents 架构 | [`engines/agents/AGENTS.md`](../AGENTS.md) |
| 风格规范 | [`.agents/rules/engines-code-style.md`](../../../.agents/rules/engines-code-style.md) |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../../../.agents/skills/engines-agents-style-check/) |
| 语音引擎（调用方） | [`../realtime_vocie/AGENTS.md`](../realtime_vocie/AGENTS.md) |