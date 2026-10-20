## REMOVED Requirements

### Requirement: 角色执行过程实时写入过程日志
**Reason**: 该过程日志由旧三角色引擎写入，引擎删除后不再产生。
**Migration**: SOP 运行日志继续写入现有的 `logs/agents/agent_events.log`，不另建一份三角色日志。

### Requirement: 过程日志的文件与自动创建
**Reason**: 旧的 `agents.log` 写入器随引擎删除。
**Migration**: 不恢复该文件。现有事件日志的路径与创建方式不变。

### Requirement: 三角色中文思考与回复
**Reason**: 规划、执行、验收三份旧角色不再运行。
**Migration**: SOP 角色的过程记录保持现有事件日志口径。

### Requirement: 过程日志不含图片二进制
**Reason**: 旧过程日志不再写入。
**Migration**: 事件日志继续不得写入图片二进制；本单不改该文件的格式。
