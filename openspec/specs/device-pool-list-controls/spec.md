# device-pool-list-controls Specification

## Purpose
定义设备管理列表页控制区：表格是唯一视图、每页行数固定、分页条常驻且左右分布、状态筛选收进下拉、名称搜索与筛选叠加，使「找设备」和「翻页」都发生在同一行控件里。

## Requirements

### Requirement: Table is the only view

设备管理页 SHALL 只呈现表格视图。页面 MUST NOT 提供「表格 / 卡片」视图切换控件，MUST NOT 渲染卡片网格、卡片分组标题或卡片操作入口。随卡片视图存在的模块内组件与常量（卡片卡片外壳、卡片分组配置、视图模式状态）MUST 一并退役，SHALL NOT 保留成无人消费的死代码。

#### Scenario: No view switch on the page

- **WHEN** 打开 `/devices`
- **THEN** 页面上没有「表格」「卡片」两个切换键，也没有任何等价的视图切换控件
- **AND** 设备数据只以表格一种形式呈现

#### Scenario: Card view artifacts are gone

- **WHEN** 检索 device-pool 模块的卡片视图相关代码
- **THEN** 不存在设备卡片组件、卡片分组配置与视图模式状态
- **AND** 模块 `index.vue` 不再引用这些符号

### Requirement: Page size is fixed at seven and the size picker is gone

设备列表每页 SHALL 固定 7 行，取值 MUST 来自模块 `constants.ts`（选项集与默认值同源），SHALL NOT 在页面内联行数字面量。页面 MUST NOT 渲染「显示行数」一类的行数选择控件。

#### Scenario: Seven rows per page

- **WHEN** 打开 `/devices` 且设备总数多于 7 台
- **THEN** 表格每页呈现 7 行数据

#### Scenario: No page-size picker

- **WHEN** 检查页面控制区
- **THEN** 不存在「显示行数」按钮组或行数下拉
- **AND** 每页行数仍由模块 `constants.ts` 的选项集单值提供

### Requirement: Pagination bar is permanent and split left/right

分页条 MUST 常驻显示（含只有 1 页或 0 台设备时）。分页文案 MUST 位于左侧，内容为「第 X / Y 页 · 共 N 台」；「上一页」「下一页」MUST 位于右侧。首页时「上一页」MUST 置灰不可用，末页时「下一页」MUST 置灰不可用；只有 1 页时两键 MUST 同时置灰但仍可见，SHALL NOT 隐藏整条分页条。置灰态 MUST 与可用态在视觉上可区分。

#### Scenario: First and last page disable the proper key

- **WHEN** 设备共 20 台、每页 7 行（3 页），用户停在第 1 页
- **THEN** 「上一页」置灰且点击无效果，「下一页」可用
- **AND** 文案为「第 1 / 3 页 · 共 20 台」

#### Scenario: Single page keeps the bar and disables both keys

- **WHEN** 设备只有 3 台（1 页）
- **THEN** 分页条仍然显示，文案为「第 1 / 1 页 · 共 3 台」
- **AND** 两个翻页键都置灰

#### Scenario: Empty list keeps the bar

- **WHEN** 没有任何设备（或筛选后无结果）
- **THEN** 分页条仍然显示「第 1 / 1 页 · 共 0 台」，两键置灰

### Requirement: Status filter is a dropdown with counts

状态筛选 MUST 是下拉控件（不是并排的 Tab 按钮组），选项 MUST 为「全部设备 / 在线 / 使用中」且各自带有当前条数。控件位置 MUST 在分页文案右侧。切换选项 MUST 只改变表格呈现的行并回到第 1 页；选项集合与其标签 MUST 来自模块 `constants.ts`。

#### Scenario: Dropdown sits right of the page text

- **WHEN** 打开 `/devices`
- **THEN** 分页文案右侧是一个下拉筛选，默认显示「全部设备」及其条数

#### Scenario: Switching the filter scopes rows and resets page

- **WHEN** 用户停在第 2 页，把筛选从「全部设备」切到「在线」
- **THEN** 表格只显示在线设备，页码回到第 1 页
- **AND** 筛选计数与当前设备数据一致

### Requirement: Name search narrows the list and stacks with the filter

列表 MUST 提供名称搜索框，位置 MUST 在筛选下拉右侧。输入内容 MUST 按「品牌 + 型号」「序列号」「连接地址」任一命中做**不区分大小写**的包含匹配。搜索 MUST 与状态筛选同时生效（交集），且搜索内容变化 MUST 让页码回到第 1 页。搜索框 MUST 可一键清空，清空后 MUST 恢复未被搜索收窄的列表。无命中时 MUST 呈现「没有匹配的设备」空态，MUST NOT 显示成「还没有可用设备」。

#### Scenario: Search matches model, serial or address

- **WHEN** 用户在搜索框输入 `sm-s9010`、`R5CT209L2QJ` 或 `10.162.93`
- **THEN** 三种输入都能筛出对应的那台设备

#### Scenario: Search stacks with the status filter

- **WHEN** 筛选为「在线」且搜索框有内容
- **THEN** 列表只包含「同时是在线且命中搜索」的设备

#### Scenario: Clearing the search restores the list

- **WHEN** 用户清空搜索框
- **THEN** 列表恢复为当前筛选下的全部设备，页码回到第 1 页

#### Scenario: No match shows the filtered empty state

- **WHEN** 搜索词没有命中任何设备
- **THEN** 空态文案为「没有匹配的设备」，并提示可清空搜索条件
- **AND** 不显示「还没有可用设备」

### Requirement: 控制条的筛选与搜索是输入件皮肤

设备管理页控制条里的状态筛选下拉与名称搜索框 MUST 呈现为输入件，不得套用按键皮肤：MUST NOT 带硬偏移影，字重 MUST 为常规（不是按键的粗字），圆角 MUST 取输入框刻度 `--app-radius-sm`（`4px 8px`）。两件的底色 MUST 为 135° 斜向渐变填充，颜色浓度从 45% 过渡到 20%，色相 MUST 取模块色 `--c-device`（薄荷绿）并通过 `--comp-device-field-fill` 派生，MUST NOT 新增颜色原子或写字面量色值。边框 MUST 保留 `2px` 墨色以与主题输入框一致。hover 时边框 MUST 转为 `--c-dashboard`；focus 时 MUST 额外出现 `3px` 柠黄低浓度扩散环。同一控制条里的「局域网」「刷新」「上一页」「下一页」MUST 继续走按键皮肤（墨边 + 硬偏移影 + 粗字）。

#### Scenario: 两个输入件不再是按键外观

- **WHEN** 打开 `/devices` 并观察控制条
- **THEN** 「全部设备 · N」下拉与搜索框都没有硬偏移影、字重为常规、圆角为 `4px 8px`
- **AND** 两件底色为从左上到右下的薄荷绿渐变，浓度由 45% 递减到 20%

#### Scenario: 输入件与按键一眼可分

- **WHEN** 同一控制条内并排观察「刷新」键与搜索框
- **THEN** 「刷新」键仍是墨边 + `2px` 硬影 + 粗字
- **AND** 搜索框无影、常规字重、带渐变填充

#### Scenario: hover 与 focus 沿用主题输入框语言

- **WHEN** 鼠标移到搜索框上
- **THEN** 边框转为柠黄 `--c-dashboard`，控件不位移、不加影
- **WHEN** 焦点进入搜索框
- **THEN** 除边框转柠黄外，外侧出现 `3px` 柠黄低浓度扩散环
