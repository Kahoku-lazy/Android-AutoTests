## REMOVED Requirements

### Requirement: 每一步由 SOP 步骤承载
**Reason**: 这条把步骤数绑在规划模型的产出上，旧引擎删除后不再成立。
**Migration**: 步骤来自 YAML，并由 `sop-task-run` 按文件顺序执行。

### Requirement: 执行者与验证者经适配器接入
**Reason**: 适配器属于旧引擎。
**Migration**: 执行与验收角色仍由 `engines/agents` 的 SOP 装配，见 `agent-sop-runner`。

### Requirement: 运行状态可持久化与续跑
**Reason**: 该续跑口径属于旧引擎步骤对象。
**Migration**: SOP 运行状态仍按 `agent-sop-runner` 与 `agent-sop-workflow`。平台任务关闭与重新执行不改。

### Requirement: 步骤级进度接入平台
**Reason**: 进度来源改为 SOP 运行结果。
**Migration**: 任务终态与加载结论见 `sop-task-run`。

### Requirement: 既有结果与证据口径保持不变
**Reason**: 该条用于保证旧引擎改造不改变证据。旧引擎删除后无从保持。
**Migration**: 任务详情的执行结果与验收展示仍由 `ai-executor-output` 与 `ai-verifier-output` 中未收回的需求约束。
