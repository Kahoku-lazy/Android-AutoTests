# frontend-doodle-kpi-card Specification

## Purpose

定义前端共享统计卡（KPI 紧凑卡与仪表盘入口卡）在 Hand-Drawn Doodle 主题下的可见行为、双变体契约与无障碍要求，保证各模块指标展示同一套卡壳语言。

## Requirements

### Requirement: Shared KPI card uses doodle shell

系统 MUST 通过共享统计卡组件呈现指标，其默认外观 SHALL 采用 Hand-Drawn Doodle 卡壳：虚线描边、近直角圆角、无模糊的色块硬偏移阴影，以及模块 accent 色；SHALL NOT 再使用实线细边 + 大圆角 + 模糊 elevation 作为该组件的默认样式。

#### Scenario: Default kpi card renders doodle shell

- **WHEN** 页面渲染共享统计卡且未指定 `entry` 变体
- **THEN** 卡片可见虚线边框、近直角圆角与硬偏移色阴影
- **AND** accent / 阴影色来自传入的模块色（或等价 CSS 变量）

#### Scenario: Existing kpi props remain compatible

- **WHEN** 既有调用方仅传入 label、value、color、shape，并可选监听 click
- **THEN** 卡片仍展示标签与数值，shape 装饰仍可区分卡片
- **AND** 点击时仍触发原有 click 行为

### Requirement: Entry variant for dashboard navigation stats

共享统计卡 MUST 提供 `entry` 变体，用于仪表盘类「指标 + 跳转」入口；该变体 SHALL 展示图标区、标题、主数值与描述文案。可导航时 MUST 只通过**整卡激活**（点击卡片、键盘 Enter/Space）跳转，MUST NOT 在卡片内再渲染独立的「进入」按钮或同类进入控件；不可导航时卡片 MUST NOT 呈现可点击的交互形态。

#### Scenario: Dashboard workflow card as entry variant

<!-- 场景名沿自变更前：工作流卡已随页面流模块退役删除，本场景改为以「在线设备」卡守住 entry 变体的整卡激活契约 -->

- **WHEN** 仪表盘以 `entry` 变体渲染「在线设备」统计入口，并提供导航目标 `/devices`
- **THEN** 卡片展示标题、主数值与描述，且不出现「进入」按钮
- **AND** 激活整卡 SHALL 导航到对应模块路径

#### Scenario: Live indicator on entry card

- **WHEN** `entry` 变体启用 live 指示
- **THEN** 卡片展示可见的 live 状态标记
- **AND** 在 `prefers-reduced-motion: reduce` 下 live 标记 MUST NOT 依赖持续动画才能被理解

### Requirement: Optional doodle decorations

共享统计卡 SHALL 支持可选装饰（如图钉、胶带），装饰 MUST NOT 遮挡标题、数值或整卡激活区域的可读性与可点区域。

#### Scenario: Decoration do not block interaction

- **WHEN** 卡片启用图钉或胶带装饰且为可点击 `entry` 卡
- **THEN** 用户点击卡面任意非装饰区域仍可激活跳转
- **AND** 主数值与标题保持可读

### Requirement: Reduced motion and keyboard access

可点击的共享统计卡 MUST 支持键盘激活；在用户启用减少动效时，卡片 MUST NOT 依赖倾斜或位移动画来传达可交互性。

#### Scenario: Keyboard activation for clickable card

- **WHEN** 可点击统计卡获得焦点且用户按下 Enter 或 Space
- **THEN** 系统执行与主键击相同的导航或 click 行为

#### Scenario: Reduced motion disables tilt animation

- **WHEN** 用户环境为 `prefers-reduced-motion: reduce`
- **THEN** 卡片悬停/入场 MUST NOT 播放依赖旋转或位移动效的反馈
- **AND** 卡片仍保持 doodle 静态壳样式（虚线边与硬阴影）

### Requirement: Dashboard consumes shared entry card

仪表盘统计入口 MUST 使用共享统计卡的 `entry` 变体（直接使用或薄包装），SHALL NOT 再维护一套与共享卡视觉不一致的私有「清新风」统计卡样式作为默认实现。

#### Scenario: Dashboard stats row uses shared doodle entry cards

- **WHEN** 用户打开仪表盘并看到统计入口行
- **THEN** 各入口卡视觉与共享 doodle `entry` 卡一致
- **AND** 不再出现与 doodle 壳冲突的默认大圆角模糊阴影统计卡样式

### Requirement: 仪表盘信息层级字号

仪表盘页面 MUST 使用三档字号表达层级：大标题（平台概览 / AI 用量等章节标题）20px；卡片与区块标题 16px；其余文本（描述、字段名、时间、标签）14px。

大标题与数值（如 KPI 的 28px 数字）MUST NOT 因本口径改动。

图表内部绘制文字（ECharts 轴标签与图例）不在本要求范围内。

#### Scenario: 卡片标题与正文分档

- **WHEN** 用户打开仪表盘
- **THEN** 「在线设备」「DEEPSEEK 账单」「用量趋势」等标题为 16px
- **AND** 「核心指标实时更新」「当天用量」等文本为 14px

#### Scenario: 大标题与数值不变

- **WHEN** 用户打开仪表盘
- **THEN** 「平台概览」「AI 用量」仍为 20px
- **AND** KPI 数值仍为 28px

### Requirement: KPI 主数值取深彩渐变

共享统计卡（`kpi` 与 `entry` 两个变体）的主数值 MUST 使用传入 accent 与墨色 `--ink` 混合的同色相渐变：起点 MUST 为 accent 与墨色按 **48%** 混合，终点 MUST 为 accent 与墨色按 **30%** 混合。该渐变 MUST NOT 混入纸色，MUST NOT 出现低于 30% 或高于 48% 的 accent 浓度。

主数值与卡底（`--color-white`）的计算对比度 MUST 不低于 **4.5:1**（大字号门槛 3:1 之上再留余量）。不支持 `background-clip: text` 时，数值 MUST 回落到终点色（`accent 30% + ink`），MUST NOT 回落到透明度或纯墨色。

标题、描述、时间与字段名 MUST NOT 改用 accent 上色；卡片描边与三层硬影 MUST 继续取同一 accent。

#### Scenario: 入口卡数值取深彩渐变

- **WHEN** 仪表盘以 `entry` 变体渲染统计入口卡
- **THEN** 主数值的渐变两端分别为 accent 与墨色 48% / 30% 的混合色
- **AND** 终点色对卡白的对比度不低于 4.5:1
- **AND** 卡片硬偏移阴影仍取同一 accent

#### Scenario: 紧凑卡数值取同一区间

- **WHEN** 页面以默认 `kpi` 变体渲染共享统计卡
- **THEN** 主数值使用与 `entry` 变体相同的 48%→30% 区间
- **AND** 标题与描述保持墨色 / 次要色，不随 accent 改变

#### Scenario: 六支模块色都达标

- **WHEN** 分别用 device / ai / runner / element / case / report 六支彩笔渲染统计卡
- **THEN** 每个数值的终点色对卡白的对比度都在 7:1 以上
- **AND** 同一排卡片仍能靠色相区分，不糊成同一种深灰
