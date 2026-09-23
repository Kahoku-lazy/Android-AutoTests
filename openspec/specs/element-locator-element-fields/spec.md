# element-locator-element-fields Specification

## Purpose
定义元素定位模块的**元素字段集合**及其呈现与写入契约：工作台呈现哪些列、哪些字段可编辑、列表响应给出哪些字段、写入入参接受与拒绝什么。它是「检查器保存什么」与「元素定位显示什么、改什么」之间的唯一对齐口径。

## Requirements

### Requirement: 元素字段集合是呈现与写入的唯一口径

元素记录 MUST 由这些字段构成：缩略图、元素名称（`alias`）、序号（`seq`）、文本（`text_val`）、主定位（`primary_xpath` 与 `primary_stable`）、七项交互标志（`clickable` / `long_clickable` / `scrollable` / `checkable` / `checked` / `enabled` / `focusable`，对外统一为「交互标注」）、测试点标记（`is_test_point`）、备注（`notes`），以及元素去重键 `resource_id` 与 `bounds`。系统 MUST NOT 再把类名、内容描述、屏幕坐标与尺寸、层级深度、父内序号、候选 XPath 列表作为呈现字段；这些列 MAY 保留在库中用于历史数据与其它写入入口，但 MUST NOT 出现在元素工作台的呈现列、新增表单或列表响应里。

#### Scenario: 呈现列只有收敛后的字段

- **WHEN** 查看元素定位元素工作台的表头
- **THEN** 只有缩略图、元素名称、序号、文本、主定位、交互标注与测试点七列
- **AND** 不出现 resource-id、坐标、class、content-desc、层级、父内序号与候选 XPath 列

#### Scenario: 去重键仍参与判定但不呈现

- **WHEN** 同一页面重复写入 `resource_id` 与 `bounds` 都相同的元素
- **THEN** 系统按该去重键判定为同一元素（更新而非新增）
- **AND** 该判定不要求把 `resource_id` 或坐标作为列展示

### Requirement: 元素列表响应只返回收敛后的字段

页面元素列表响应 MUST 返回收敛后的字段（含缩略图路径、序号、主定位表达式与稳定标记、七项交互标志、元素名称、文本、测试点与备注），MUST NOT 返回候选 XPath 列表；由于元素定位不再保存也不关联整屏截图，响应 MUST NOT 再返回页面截图路径。

#### Scenario: 列表响应字段齐备且无候选列表

- **WHEN** 客户端请求某页面的元素列表
- **THEN** 每条元素含缩略图路径、序号、主定位表达式、七项交互标志、元素名称、文本与测试点
- **AND** 响应中不含候选 XPath 列表字段，也不含页面截图路径

### Requirement: 元素字段的必填与拒绝口径

元素写入的两条入口共享同一必填口径。**新增**时元素名称必填、`resource_id` 与 `bounds` MUST 至少一个非空：缺任一必填 MUST 返回 HTTP 400 并带中文原因，MUST NOT 新增任何行。**更新**时元素名称与主定位表达式 MUST 非空：把任一已填字段提交为空串 MUST 返回 HTTP 400 并带中文原因，MUST NOT 写库，MUST NOT 用空值覆盖原值；本次未提交的字段 MUST 保持原值。手动新增命中同页既有 `(page, resource_id, bounds)` 时 MUST 返回 HTTP 409，且该原因文案 MUST 指出既有元素——包含其元素名称，既有名称亦为空时包含其 id——使用户无需逐行核对即可定位冲突对象。本要求只约束手动新增入口；去重键在设备检查器保存路径上的判定见本能力既有要求。

#### Scenario: 更新清空元素名称被拒

- **WHEN** 客户端把某元素的元素名称提交为空串
- **THEN** 返回 HTTP 400 并带中文原因
- **AND** 库中该元素的元素名称保持原值

#### Scenario: 更新清空主定位被拒

- **WHEN** 客户端把某元素的主定位表达式提交为空串
- **THEN** 返回 HTTP 400 并带中文原因
- **AND** 库中该元素的主定位保持原值

#### Scenario: 更新只提交部分字段时其余不动

- **WHEN** 客户端只提交某元素的文本新值
- **THEN** 返回成功信封且该元素文本已更新
- **AND** 该元素的元素名称、主定位与测试点保持原值

#### Scenario: 新增撞去重键时指出既有元素

- **WHEN** 客户端手动新增一个与同页既有元素 `resource_id` 与 `bounds` 都相同的元素
- **THEN** 返回 HTTP 409
- **AND** 原因文案包含既有元素的元素名称；既有名称亦为空时包含其 id
- **AND** MUST NOT 新增任何行
