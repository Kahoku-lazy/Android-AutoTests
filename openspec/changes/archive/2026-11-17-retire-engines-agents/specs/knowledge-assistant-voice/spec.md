## REMOVED Requirements

### Requirement: 浏览器与实时模型之间的音频桥接

**Reason**: 语音问答能力整体下线，实时语音模型与会话传输实现随 `engines/agents` 退役。

**Migration**: 无替代。知识库能力只保留 `engines/ae_harness/knowledge/` 的只读检索工具，不再提供语音入口。

### Requirement: 对话记录实时呈现

**Reason**: 语音页面与前端 `modules/knowledge-assistant` 一并删除。

**Migration**: 无替代。

### Requirement: 对话记录写入本地日志

**Reason**: 语音会话不再存在，其转写日志写入链路随之删除。

**Migration**: 无替代。任务与平台对话的过程日志仍由事件日志承担。

### Requirement: 就绪状态可查询

**Reason**: `backend/apps/knowledge_assistant` 整体下线，不再有语音就绪状态端点。

**Migration**: 无替代。

### Requirement: 会话结束释放全部资源

**Reason**: 语音会话对象不再存在。

**Migration**: 无替代。

### Requirement: 麦克风输入可观测且无输入可提示

**Reason**: 前端麦克风采集与语音控制台随模块删除。

**Migration**: 无替代。

### Requirement: 直接对话不注入预设答案

**Reason**: 该约束只对已下线的语音直连模式有意义。

**Migration**: 无替代。

### Requirement: WebSocket 只承载知识库问答通道

**Reason**: 语音与文字问答通道均已下线，不再有知识库问答 WebSocket。

**Migration**: 无替代。路由与 consumer 一并删除。

### Requirement: 页面提供会话方式选择与启动按键

**Reason**: 语音页面删除。

**Migration**: 无替代。

### Requirement: 知识库助手 Token 用量记录

**Reason**: 知识助手不再产生会话，也就没有对应用量；平台对话与任务的用量仍写既有账本。

**Migration**: 无替代。

### Requirement: 本地知识检索由语音与文字共用

**Reason**: 语音与文字两条会话都不存在了，共用约束失去对象。

**Migration**: 知识检索只保留 `engines/ae_harness/knowledge/` 的只读工具形态，由调用方按需挂载。
