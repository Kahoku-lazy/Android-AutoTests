## REMOVED Requirements

### Requirement: AiEngine 协议接口
**Reason**: 控制设备任务不再经可替换旧引擎执行。
**Migration**: 任务启动改由 `sop-task-run` 规定。

### Requirement: TaskRequest 契约
**Reason**: 平台不再组装旧引擎请求。
**Migration**: 执行与验收模型按 `sop-task-run` 的启动组装交给 SOP。

### Requirement: TaskResult 归一化
**Reason**: 旧引擎不再返回结果。
**Migration**: 任务终态仍由 SOP 运行结果写回，口径见 `sop-task-run`。

### Requirement: 引擎零 apps 依赖
**Reason**: 该约束只约束即将删除的旧引擎。
**Migration**: SOP 与设备工具继续遵守各自现有需求，不恢复旧引擎。

### Requirement: 引擎注册与 fail-fast
**Reason**: 不再按引擎名加载旧实现。
**Migration**: 无替代注册表。任务失败条件见 `sop-task-run`。

### Requirement: 装配期配置 fail-fast
**Reason**: 三角色装配不再作为任务入口。
**Migration**: 只校验执行与验收，见 `sop-task-run`「启动时组装执行与验收模型」。

### Requirement: provider 配置单一真相源
**Reason**: 旧引擎侧的 provider 对照不再存在。
**Migration**: 启动 SOP 时仍只接受 DeepSeek 与阿里百炼，见 `sop-task-run`。

### Requirement: 系统提示词随引擎走
**Reason**: 旧引擎的三份提示词常量随目录删除。
**Migration**: SOP 提示词仍由 `agent-sop-runner` 约束，不从数据库读取。

### Requirement: 引擎以框架步骤承载执行与验收
**Reason**: 这条描述的是旧引擎内部编排。
**Migration**: 平台步骤编排以 `sop-task-run` 与 `agent-sop-workflow` 为准。
