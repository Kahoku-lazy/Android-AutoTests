# workflow/voice AGENTS.md

> 层级：根 `AGENTS.md` → `engines/AGENTS.md` → `engines/agents/AGENTS.md` → **本文件**。

本目录是语音助手交给前后端的**唯一出口**。不创建模型，不直接构造 `RealtimeAgent`。

| 文件 | 职责 |
| --- | --- |
| `__init__.py` | 再导出打开会话、就绪状态、浏览器音频传输、转写桥 |

内部实现仍在 `engines/agents/realtime_vocie/`。`backend/` 与 `knowledge_chat/` MUST NOT 直接 import 那个包。

红线：

1. MUST NOT import `backend.apps` / `django`。
2. MUST NOT 在本目录构造 `RealtimeAgent`。智能体只由 `assistant.create_voice_agent` 创建，调用发生在内部会话。
3. 音频传输由调用方持有。本出口不关闭浏览器通道。
4. 不改 WebSocket 路径、事件类型和对话日志位置。
