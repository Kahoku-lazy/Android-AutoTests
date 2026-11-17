## REMOVED Requirements

### Requirement: planner 装配页面流工具子集

**Reason**: 页面流模块整体退役，`list_page_flows` / `get_page_flow` 工具的实现已在此前退役变更中删除，planner 不再有页面流资产可读。

**Migration**: planner 工具子集不再包含页面流工具；executor 与 verifier 的子集本就不含页面流工具，不受影响。log_check 相关要求保留不动。

### Requirement: planner 默认提示词含页面流阅读指引

**Reason**: 页面流模块整体退役，提示词中「先列出页面流、再读语义摘要」的指引指向不存在的工具，必须移除以免模型调用不存在的工具。

**Migration**: 引擎提示词常量中的页面流阅读指引随实现清理删除（历史迁移文本不改写）；log_check 指引保留。

### Requirement: 规划读取的页面流摘要只含页面与节点关系

**Reason**: 页面流语义摘要出口（`get_page_flow` → `build_graph_digest`）随模块整体删除，摘要内容约束不再有承载实现。

**Migration**: 无。
