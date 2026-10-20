## REMOVED Requirements

### Requirement: 起点只提供「启动 App」与「起始页面」两种模式

**Reason**: 「起始页面」模式的内容来源是元素定位页面（`linked_page_id` / `linked_page_name` / `linked_elements`），元素定位退役后该模式无数据源。
**Migration**: 起点只保留「启动 App」。存量 `start_kind=page` 的文档 MUST 按「启动 App」模式降级呈现，画布 MUST NOT 报错；与既有 `url` / `api` 降级同口径。

### Requirement: 起点模式数据契约收敛为 app / page

**Reason**: `page` 模式的数据契约（`linked_page_id` / `linked_page_name` / `linked_elements`）整体指向元素定位库，库退役后契约无承载。
**Migration**: `start_kind` 只允许 `app`。存量文档的四个关联键（`linked_elements` / `linked_page_domain` / `linked_page_id` / `linked_page_name`）由数据迁移清空。

## ADDED Requirements

### Requirement: 起点只提供「启动 App」一种模式

页面流画布的起点节点 MUST 只提供「启动 App」一种模式，MUST NOT 提供「起始页面」模式、URL 模式或 API 模式，也 MUST NOT 渲染页面关联、URL、API 参数输入框。「启动 App」模式 MUST 只以 `properties.package_name` 承载包名，起点 MUST NOT 写入 `start_url` / `start_api` / `linked_page_id` / `linked_page_name` / `linked_elements`。历史文档遗留的 `start_kind` 为 `page` / `url` / `api` 时 MUST 按「启动 App」模式呈现，MUST NOT 使画布渲染失败。

#### Scenario: 起点的模式区只有一个按钮

- **WHEN** 用户在画布上查看起点节点的模式区
- **THEN** 只出现「启动 App」一个按钮，不存在「起始页面」「URL」「API」按钮

#### Scenario: 历史 page 起点降级呈现

- **WHEN** 打开一篇 `start_kind` 为 `page` 的历史页面流文档
- **THEN** 该起点按「启动 App」模式呈现，画面不报错，不出现页面关联输入框

#### Scenario: 启动 App 模式的起点属性

- **WHEN** 起点处于「启动 App」模式并填入包名
- **THEN** `properties.start_kind` 为 `app`，包名写入 `properties.package_name`，起点保留单一「启动」输出口且无其它模式键
