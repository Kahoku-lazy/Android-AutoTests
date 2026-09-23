# ai-device-planner-tools Specification

## Purpose
让设备执行链路的规划模型（planner）在规划阶段能读到平台的页面流文档（可列出全部文档并读取单篇语义摘要），并在默认提示词里被告知去读取它们，使规划能依托既有页面流资产；同时保证三个角色的工具子集只引用已注册工具，避免因静默跳过缺失名而漏装配。

## Requirements

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
- **THEN** executor 仍为原设备控制工具集，verifier 仍仅为 `screenshot_page`

### Requirement: planner 默认提示词含页面流阅读指引

设备执行链路 planner 的默认系统提示词 MUST 指引模型先列出页面流文档、再按需读取某篇的语义摘要，且 MUST 只使用已注册的工具名与参数。该指引 MUST 随迁移下发到存量库：仅当字段仍含平台原文锚点且尚未出现该指引时才写入，管理员已改写过的提示词 MUST NOT 被覆盖。指引的写入 MUST 可逆。

#### Scenario: 新装库的 planner 提示词含指引

- **WHEN** 全新安装后读取平台智能体的 planner 提示词
- **THEN** 其中含「先 `list_page_flows` 列出页面流、需要细节用 `get_page_flow`」的指引
- **AND** 只出现已注册的工具名

#### Scenario: 存量库同步指引

- **WHEN** 存量库的 planner 提示词仍是平台原文（含锚点、且未含该指引）
- **THEN** 迁移后该提示词含指引，其余内容不变（逐字保留）

#### Scenario: 用户改写过的提示词不被覆盖

- **WHEN** 管理员已改写过 planner 提示词（锚点已不存在）
- **THEN** 迁移不修改该字段

#### Scenario: 指引写入可逆

- **WHEN** 回滚该迁移
- **THEN** 追加的指引条目被移除，提示词回到迁移前的内容
