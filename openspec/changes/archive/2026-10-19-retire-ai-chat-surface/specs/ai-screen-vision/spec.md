## REMOVED Requirements

### Requirement: 截图在对话历史中持久化

**Reason**: 会话/消息表已删除，平台不再有对话历史，截图无法也不应再挂到消息块上。
**Migration**: 截图改由任务步骤证据承载（任务过程记录中的验证截图路径 + `media/device_inspector/screenshots/` 落盘文件）；工具调用结果仍可即时回传给模型。
