## Why

上一版 RAG 只接了 Pipeline 的 DeepSeek。用户要求 Omni 直连也能依据 `rag_data` 回答。Omni 是端到端实时模型，没有独立文本 LLM 可注入上下文，因此改为给 `RealtimeAgent` 注册 `search_knowledge` 工具：模型在需要时调用工具检索，再把结果组织成语音回答。

## What Changes

- 新增 `engines/agents/rag/tool.py`：`build_rag_tool()` 把 `RagService` 包装成只读 `search_knowledge` 工具。
- `RealtimeVoiceSession` 在 `omni` 模式下创建 RAG 工具并注册到 `RealtimeAgent`；系统提示要求产品资料问题先检索。
- Omni 的 `ready` 事件带 `rag_enabled`；工具检索失败只返回“没有相关资料”，不中断会话。
- Pipeline 的上下文注入保持不变；两条路线共用同一个 `RagService`/索引。

## 关联文档

- 已归档 `2026-10-28-add-rag-voice-llm`
- AgentScope 2.0.10 RAG 教程
- DashScope `qwen3.5-omni-plus-realtime` 模型卡支持工具调用

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: RAG 从「仅 Pipeline」扩展到「Pipeline 注入 + Omni 工具调用」。

## Impact

- 引擎：新增 `rag/tool.py`；`session.py` 注册 Toolkit/工具。
- 后端：无新接口；WS 不变。
- 前端：无结构改动，`ready.rag_enabled` 为附加字段。
- 测试：工具构造、Omni 真实语音 RAG 检索、Pipeline 回归。
