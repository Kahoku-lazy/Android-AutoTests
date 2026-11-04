# knowledge_chat AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md`、[`engines/AGENTS.md`](../../AGENTS.md)、[`engines/agents/AGENTS.md`](../AGENTS.md) 优先于本文件（本文件只写增量）。

## 职责

知识库助手的**文字问答**会话（DeepSeek Flash + 本地知识检索），只被 `backend/apps/knowledge_assistant` 接入；语音会话在 [`realtime_vocie`](../realtime_vocie/AGENTS.md)，两者不共享上下文。

| 文件 | 职责 |
| --- | --- |
| `config.py` | 模型名（目录短名 `deepseek_flash`）、文本长度上限、`text_ready` / `text_reason` |
| `session.py` | `KnowledgeChatSession`：回显用户消息 → 流式回答 → 落日志；`build_chat_toolkit()` 按 RAG 开关装 `search_knowledge` |

## 红线

1. **engines 不 import django / `backend.apps`**；本包只被后端接入。
2. **提示词不复制**：正文在 `config/data/prompts/KNOWLEDGE_CHAT_PROMPT.md`，经 `role_sys_prompts.KnowledgeChatPrompts` 取。
3. **检索不另建一套**：只经 `engines.agents.rag` 的 `search_knowledge` 工具，与语音共用同一份索引。
4. **纯文字**：装配时 `with_tts=False`，不下发音频、不引入播放链路。
5. **上下文不跨连接**：每次连接一个 Agent 实例，连接结束即丢弃；MUST NOT 落库或跨会话复用。

## 快速验证

```powershell
python -c "from engines.agents.knowledge_chat import KnowledgeChatSession, build_status; print(build_status())"
python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_chat_session.py -q
```
