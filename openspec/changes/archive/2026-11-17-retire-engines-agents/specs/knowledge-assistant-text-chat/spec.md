## REMOVED Requirements

### Requirement: 页面提供语音与文字两种会话方式

**Reason**: 知识助手页面整体下线，`/knowledge-assistant` 路由与侧栏入口一并删除。

**Migration**: 无替代。侧栏「AI 功能」分组只保留「AI 助手」。

### Requirement: 文字提问复用同一条知识库通道

**Reason**: 文字问答会话实现随 `engines/agents/knowledge_chat` 退役。

**Migration**: 无替代。

### Requirement: 文字会话使用 DeepSeek Flash 与本地知识检索

**Reason**: 文字会话不再存在；模型与角色配置统一收敛到 `ae_harness` 的 `models.yaml` 与提示词文件。

**Migration**: 无替代。知识检索如需使用，只经 `ae_harness/knowledge` 的只读工具挂到执行者角色上。

### Requirement: 文字会话的多轮上下文只在本次连接内

**Reason**: 会话对象失去宿主。

**Migration**: 无替代。

### Requirement: 文字入口的就绪状态独立可查

**Reason**: `backend/apps/knowledge_assistant/runtime.py` 随 app 删除，状态端点不再存在。

**Migration**: 无替代。

### Requirement: 文字对话写入日志与用量账本

**Reason**: 文字会话不再产生对话与用量。

**Migration**: 无替代。平台对话（`platform_ui`）的用量仍写既有账本，不受影响。
