## REMOVED Requirements

### Requirement: 知识库语音经 workflow 出口接入

**Reason**: 知识助手（实时语音 + 文字问答）产品面已整体下线，退役门禁（`utils/check_gates.py` 的 `engines-agents-retirement`）已禁止 `backend/apps/knowledge_assistant` 与 `frontend/src/modules/knowledge-assistant` 复活；后端 `backend/gateway/routing.py` 的 `websocket_urlpatterns` 为空，无任何 WebSocket 生产点。本规格描述的 `/ws/knowledge-assistant/` 语音通道属孤儿文档，随前端 `/ws` 死代理退役一并移除。

**Migration**: 无需迁移——该语音面已无前端客户端与后端 consumer，无在线调用方。将来若重新引入 WebSocket 需求，按 `backend/gateway/routing.py` 注释登记新 consumer 并另立 OpenSpec 变更，不复用本已下线规格。
