## REMOVED Requirements

### Requirement: 平台任务按三模型工作流执行
**Reason**: 任务线程只启动 SOP，不再跑规划、执行、验收三模型工作流。
**Migration**: 新建任务按 `sop-task-run` 启动。不再提供单独的平台三模型任务。

### Requirement: 平台任务使用平台工具
**Reason**: 该工具子集只服务于已删除的三模型工作流。
**Migration**: SOP 工具以引擎代码为准，见 `sop-task-run`。装配台调试入口保持不变。

### Requirement: 平台写工具自动放行
**Reason**: 自动放行只作用于已删除的三模型任务。
**Migration**: 不把该放行规则加到 SOP。调试页的写工具权限保持原需求。

### Requirement: 平台任务全用文本模型
**Reason**: 不再创建平台任务的三个文本模型。
**Migration**: 控制设备任务的执行与验收模型按线路配置，见 `sop-task-run`。
