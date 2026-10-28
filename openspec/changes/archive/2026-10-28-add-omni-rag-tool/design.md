## Context

`qwen3.5-omni-plus-realtime` 的模型卡 `supports_tools=True`；`RealtimeAgent` 接受 `Toolkit`，会把工具 schema 放进 `session.update`，执行工具后继续生成回复。RAG 已有 `RagService.build_context()`，可直接包装为工具。

## Decisions

### 1. 工具而不是提示词注入

Omni 没有“每轮 user 文本”可注入的独立 LLM；把全部资料塞进系统提示既不动态也超长。注册 `search_knowledge(query)`，由模型按需调用。

### 2. 工具只读、无人工确认

`FunctionTool(is_read_only=True, permission=ALLOW)`；工具只读本地索引，不写文件、不调平台 API。

### 3. 共用同一个 RagService/索引

Pipeline 与 Omni 都 `RagService.from_env()`；SQLite 索引与增量状态共用，避免两套索引。

### 4. 失败降级

工具捕获/返回“没有检索到资料”，不抛给 RealtimeAgent；索引失败时 `RagService.search` 返回空，模型继续自由回答。

## Risks

- [模型不调用工具] → 系统提示明确产品资料先检索；实测按键问题会调用。
- [工具调用增加延迟] → 首次索引约 1–2 秒，之后 SQLite 检索毫秒级。
- [工具结果过长] → `RagService` 已有 `max_context_chars=3000` 截断。
