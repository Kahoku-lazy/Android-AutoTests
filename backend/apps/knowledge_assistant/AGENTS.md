# knowledge_assistant AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/AGENTS.md` 优先于本文件（本文件只写增量）。

## 边界

- HTTP：`GET /api/knowledge-assistant/status/` 返回就绪状态（无密钥）。
- WS：`/ws/knowledge-assistant/?token=<access_token>` 是平台**唯一**实时语音通道；只承载本会话的音频、转写、打断与播放进度。
- **AgentScope 相关实现**（实时模型配置/工厂、提示词、事件桥、`RealtimeAgent` 会话、`TransportBase` 传输）一律放 `engines/agents/realtime_vocie`；本 App 只做鉴权、WS 接入与本地对话日志。
- 产品路径**仅** `omni` + 知识库 RAG（`RealtimeVoiceSession`）；livetranslate / pipeline 已移除。

## 红线

1. **RAG 边界**：允许 `engines/agents/rag` 读取本地资料并注入 Omni 会话工具；不得引入文档上传 UI、平台知识库写接口、外部向量库服务。
2. **engines 红线**：本 App 可 import engines；engines **不得** import django / `backend.apps`。
3. **不接 channel layer** 做音频帧转发。
4. **WS 白名单**：客户端只能发 `interrupt` 与 `played`；不得把任务、设备、文件或平台写操作接进本通道。
5. **不得重新引入** mode 选择器或 pipeline / livetranslate 会话分支。
