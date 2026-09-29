## MODIFIED Requirements

### Requirement: planner 装配页面流工具子集

设备执行链路的 planner MUST 装配页面流工具 `list_page_flows` 与 `get_page_flow`，使其在规划阶段能列出页面流文档并读取单篇语义摘要。该子集 MUST 只引用已注册的平台工具——工具装配按名取子集、对缺失名静默跳过，含未注册名的子集会导致静默漏装配而不报错。executor 与 verifier 的工具子集 MUST NOT 因本要求发生变化。

#### Scenario: planner 可见页面流工具

- **WHEN** 设备执行链路装配 planner
- **THEN** planner 的工具子集含 `list_page_flows` 与 `get_page_flow`

#### Scenario: 子集不引用未注册工具

- **WHEN** 检查 planner / executor / verifier 三个工具子集
- **THEN** 其中每个工具名都存在于平台工具注册表
- **AND** 仓库内工具手册所述的角色子集与代码一致

#### Scenario: 其它角色子集不受影响

- **WHEN** 检查 executor 与 verifier 的工具子集
- **THEN** executor 仍为原设备控制工具集（含通用日志查询）；verifier 仍为「截图工具」加它按另有要求装配的只读日志检查工具（见 `device-log-read-tool`），本要求 MUST NOT 改变其中任何一项
