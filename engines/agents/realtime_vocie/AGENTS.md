# realtime_vocie AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `engines/agents/AGENTS.md` 优先于本文件（本文件只写增量）。

## 产品路径

本包**只保留 Omni 实时语音 + 知识库问答（RAG）**：

- `DashScopeRealtimeModel` / `RealtimeVoiceSession` / WebSocket transport / events bridge
- Omni 会话上注入 `engines.agents.rag` 检索工具（见 `session.py`）
- 系统提示词在 `knowledge.py`

**已移除**：`livetranslate`、`pipeline`（ASR→DeepSeek→TTS）、相关模式切换与配置分支。

**文字问答**不在本包：见 [`knowledge_chat/AGENTS.md`](../knowledge_chat/AGENTS.md)（DeepSeek Flash + 同一 RAG 工具，不共享上下文、不下发音频）。

## 模块一览

| 文件 | 职责 |
|------|------|
| `config.py` | `RealtimeVoiceConfig` / `load_config` / `create_realtime_model` / 就绪状态（仅 omni） |
| `knowledge.py` | 知识库问答系统提示词 |
| `session.py` | `RealtimeVoiceSession`：Omni RealtimeAgent + RAG toolkit |
| `events.py` | 转写 / 状态事件桥与用量落盘 |
| `transport.py` | 浏览器 PCM 音频传输 |
| `role/realtime_vocie_agent.py` + `OMNI_ROLE_CONFIG` | 角色侧 Omni 配置（与本包会话路径对齐，勿破坏 UI 角色） |

## 红线

1. **engines 不 import django / `backend.apps`**。
2. **不直连浏览器**：本包只被 `backend/apps/knowledge_assistant` 接入。
3. **不复制提示词到后端**：直接对话提示词只在本包 `knowledge.py` 维护。
4. **会话释放**：`RealtimeVoiceSession` 必须保证 `session_end` 落盘与看门狗取消。
5. **Token 记录**：Omni 从 `ModelCallEndEvent` 写 `model_usage`。
6. **不得重新引入** livetranslate / pipeline 模式或模式选择器。

## 快速验证

```powershell
python -c "from engines.agents.realtime_vocie import RealtimeVoiceSession, load_config; print('ok')"
pytest tests/graybox/unit/test_knowledge_assistant_config.py tests/graybox/unit/test_realtime_vocie_models.py -q
```
