## REMOVED Requirements

### Requirement: planner 装配页面流工具子集
**Reason**: 控制设备任务不再装配规划模型。
**Migration**: 步骤来自 YAML，见 `sop-task-run`。页面流工具不再因本需求进入任务。

### Requirement: planner 默认提示词含页面流阅读指引
**Reason**: 规划模型提示词随旧引擎删除。
**Migration**: 无替代规划提示词。

### Requirement: 规划模型标注需日志核对的步骤
**Reason**: 不再由规划模型给步骤打日志核对标记。
**Migration**: 日志检查仍由 SOP 验收侧的现有日志工具需求约束。

### Requirement: 规划默认提示词含日志核对标记指引
**Reason**: 规划提示词文件删除。
**Migration**: 无替代规划提示词。

### Requirement: 规划读取的页面流摘要只含页面与节点关系
**Reason**: 规划阶段的页面流读取不再发生。
**Migration**: 页面流文档的保存与查询保持各自现有需求，不从本需求触发。
