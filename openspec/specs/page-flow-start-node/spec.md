# page-flow-start-node Specification

## Purpose
定义页面流画布起点节点的模式与参数边界：起点只有「启动 App」一种模式（需包名），「起始页面」随元素定位退役删除，使画布不再残留页面关联、URL / API 模式。

## Requirements
### Requirement: 起点语义摘要不输出 URL / API 字段
页面流语义摘要（AI 只读出口）对起点节点 MUST 只输出 `start_kind` 与（有值时）`package_name`，MUST NOT 输出 `start_url` / `start_api` 字段。

#### Scenario: 起点摘要字段收敛
- **WHEN** 读取一篇含起点节点的页面流文档语义摘要
- **THEN** 该起点条目含 `start_kind` 与（有值时）`package_name`，不含 `start_url` 与 `start_api`

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
