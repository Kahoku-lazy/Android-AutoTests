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

### Requirement: 规划模型标注需日志核对的步骤

设备执行链路的规划模型 SHALL 为每个步骤产出一个「是否需日志核对」标记（`log_check`，布尔）：当该步的断言需要靠设备日志才能核对时标为真（例如点击开关并断言开关事件日志、断言设备上报或应答日志），当断言只看页面（页面出现某文案、进入某页面、元素状态变化）时标为假。该字段 MUST 有缺省值（假），缺失时系统 MUST 按「不需日志核对」处理且 MUST NOT 报错。规划模型 MUST NOT 把所有步骤一律标为真，MUST NOT 把与日志无关的页面断言标为真。

#### Scenario: 开关日志类断言被标记

- **WHEN** 用户需求为「点击开关，断言设备上报开关日志」
- **THEN** 该步的 `log_check` 为真

#### Scenario: 纯页面断言不被标记

- **WHEN** 某步断言为「页面进入设备详情页，标题显示 H6810」
- **THEN** 该步的 `log_check` 为假

#### Scenario: 缺省按不需日志处理

- **WHEN** 规划模型产出的某步没有给出该标记
- **THEN** 系统按不需日志核对处理，步骤照常执行，MUST NOT 因缺字段失败

#### Scenario: 取值无法解读时不报错

- **WHEN** 规划模型给出的该标记不是布尔（例如字符串、数字或空值）
- **THEN** 系统宽松归一（可读为真的取值按真处理，其余按假），步骤照常执行，MUST NOT 因该字段导致整步建模失败

### Requirement: 规划默认提示词含日志核对标记指引

设备执行链路的规划模型默认系统提示词 MUST 指引模型为每个步骤判断并给出该标记，并给出判定口径（断言需靠设备日志核对才为真）。该指引 MUST 随迁移下发到存量库：仅当字段仍含平台原文锚点且尚未出现该指引时才写入，管理员已改写过的提示词 MUST NOT 被覆盖。指引的写入 MUST 可逆。

#### Scenario: 新装库的规划提示词含指引

- **WHEN** 全新安装后读取平台智能体的规划提示词
- **THEN** 提示词含日志核对标记的判定口径与输出字段说明

#### Scenario: 存量库原文提示词被补写

- **WHEN** 存量库的规划提示词仍是平台原文（含锚点、且未含该指引）
- **THEN** 迁移把指引追加进该字段，其它内容保持不变

#### Scenario: 已改写的提示词不被覆盖

- **WHEN** 管理员已改写过规划提示词（锚点已不存在）
- **THEN** 迁移 MUST NOT 改动该字段

#### Scenario: 迁移可逆

- **WHEN** 回滚该迁移
- **THEN** 之前被追加的指引被移除，字段回到迁移前的形态
