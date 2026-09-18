# frontend-doodle-appcard-panel Specification

## Purpose

定义共享 AppCard（L3 可复用数据块）在 Hand-Drawn Doodle 主题下的钉板外观、同排 cycle accent，以及仪表盘趋势块消费方式；明确 ECharts 画布配色独立且允许硬编码。

## Requirements

### Requirement: AppCard uses pinboard doodle shell

系统 MUST 通过共享 `AppCard` 呈现可复用数据块。默认外观 SHALL 对齐 `#page-typography` 钉板：2.5px 虚线墨色描边、近直角、无模糊的色块硬偏移阴影、可选居中图钉、微倾；SHALL NOT 再使用实线大圆角 + 彩色顶条作为默认壳。

#### Scenario: Default AppCard renders pinboard shell

- **WHEN** 页面在工作台主题作用域内渲染 `AppCard`
- **THEN** 卡片可见虚线边框、近直角、硬偏移色阴影
- **AND** 默认有居中图钉装饰（可用 prop 关闭）

### Requirement: Same-row cards cycle module accents

同一行/网格内相邻 `AppCard` 的 accent（图钉色与硬阴影）MUST 按列表 index 循环模块色令牌（复用 `sketchToneAt`）。SHALL NOT 把同排卡锁成单一模块色。

#### Scenario: Adjacent AppCards use different accents

- **WHEN** 同一网格渲染不少于 2 张 AppCard 且父级注入 cycle tone
- **THEN** index 0 与 index 1 的 accent 令牌不同

### Requirement: Dashboard trend blocks use AppCard

仪表盘「趋势数据」四块（执行趋势、任务结果、Token、费用）MUST 使用 `AppCard`，SHALL NOT 继续使用裸 `el-card` 作为默认实现。

#### Scenario: Dashboard trends render AppCard pinboard

- **WHEN** 用户打开仪表盘并看到趋势数据区
- **THEN** 四块均为 AppCard 钉板壳
- **AND** 同排 accent 按 cycle 轮转

### Requirement: ECharts canvas colors may be hardcoded

ECharts 配置内的系列色、坐标轴色、区域填充等画布配色 SHALL 视为独立主题；系统 MAY 在 ECharts option 中使用字面量色值。本要求不强制 ECharts 色走 CSS 令牌。

#### Scenario: Chart option keeps independent palette

- **WHEN** 趋势图或报告图通过 ECharts 渲染
- **THEN** 画布内配色可保持既有硬编码色板
- **AND** 卡片外壳仍走 AppCard 钉板令牌
