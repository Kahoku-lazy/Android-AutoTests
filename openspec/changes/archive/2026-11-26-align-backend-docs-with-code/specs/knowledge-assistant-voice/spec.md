# knowledge-assistant-voice Delta

## REMOVED Requirements

### Requirement: 知识库语音经 workflow 出口接入

**Reason**: 知识库助手（实时语音 + 文字问答）已整体下线（归档变更 retire-engines-agents）；gateway/routing.py 为空清单，全仓无 consumer，退役门禁（utils/check_gates.py）禁止该产品面复活。本规格是归档时声称删除而实际残留的活跃 spec，正式收口。

**Migration**: 无迁移——平台不再有语音通道，任务进度与列表走 HTTP 轮询；未来若新增 WebSocket 需求，先在 gateway/routing.py 登记 consumer 并走 OpenSpec 新变更，不复用本规格。