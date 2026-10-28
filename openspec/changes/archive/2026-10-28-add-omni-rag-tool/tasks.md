## 1. 工具

- [x] 1.1 新增 `engines/agents/rag/tool.py`：`build_rag_tool()` 包装 `search_knowledge`
- [x] 1.2 `RealtimeVoiceSession` 在 omni 模式注册 Toolkit；系统提示要求产品问题先检索
- [x] 1.3 `ready` 事件带 `rag_enabled`；日志记录 rag 状态

## 2. 验证

- [x] 2.1 `build_rag_tool()` 名称/只读属性单测
- [x] 2.2 真实 WAV 走 Omni：“长按开关按键三秒”回答包含 Wi-Fi/网络待机资料内容
- [x] 2.3 Pipeline RAG 回归不退化
- [x] 2.4 ruff / pytest / manage.py check
- [x] 2.5 `openspec validate add-omni-rag-tool --strict` 并归档
