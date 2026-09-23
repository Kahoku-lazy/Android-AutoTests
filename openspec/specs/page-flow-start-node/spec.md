# page-flow-start-node Specification

## Purpose
定义页面流画布起点节点的模式与参数边界：起点只能是「启动 App」（需包名）或「起始页面」（关联 Android 页面与其元素），使 Web/API 域下线后不再残留 URL / API 模式。

## Requirements

### Requirement: 起点只提供「启动 App」与「起始页面」两种模式
页面流画布的起点节点 MUST 只提供「启动 App」与「起始页面」两种模式，MUST NOT 提供 URL 模式或 API 模式，也 MUST NOT 渲染 URL / API 参数输入框。历史文档遗留的 `url` / `api` 取值 MUST 按「启动 App」模式呈现，MUST NOT 使画布渲染失败。

#### Scenario: 起点的模式按钮只有两个
- **WHEN** 用户在画布上查看起点节点的模式区
- **THEN** 只出现「启动 App」与「起始页面」两个按钮，不存在「URL」按钮与「API」按钮

#### Scenario: 历史 url/api 起点降级呈现
- **WHEN** 打开一篇 `start_kind` 为 `url` 或 `api` 的历史页面流文档
- **THEN** 该起点按「启动 App」模式呈现，画面不报错，也不出现 URL / API 输入框

### Requirement: 起点模式数据契约收敛为 app / page
起点节点保存的 `properties.start_kind` MUST 只取 `app` 或 `page`。「启动 App」模式 MUST 只以 `properties.package_name` 承载包名；「起始页面」模式 MUST 只以 `linked_page_id` / `linked_page_name` / `linked_elements` 承载关联页面与元素目录。起点节点 MUST NOT 写入 `start_url` 或 `start_api` 属性。

#### Scenario: 启动 App 模式的起点属性
- **WHEN** 起点处于「启动 App」模式并填入包名
- **THEN** `properties.start_kind` 为 `app`，包名写入 `properties.package_name`，起点保留单一「启动」输出口且无参数之外的 URL / API 键

#### Scenario: 起始页面模式的起点属性
- **WHEN** 用户把起点切到「起始页面」模式并关联一个 Android 页面
- **THEN** `properties.start_kind` 为 `page`，`properties` 记录该页面的 id、名称与元素目录，起点无输入口，元素输出口由用户自行添加

### Requirement: 起点语义摘要不输出 URL / API 字段
页面流语义摘要（AI 只读出口）对起点节点 MUST 只输出 `start_kind` 与（有值时）`package_name`，MUST NOT 输出 `start_url` / `start_api` 字段。

#### Scenario: 起点摘要字段收敛
- **WHEN** 读取一篇含起点节点的页面流文档语义摘要
- **THEN** 该起点条目含 `start_kind` 与（有值时）`package_name`，不含 `start_url` 与 `start_api`
