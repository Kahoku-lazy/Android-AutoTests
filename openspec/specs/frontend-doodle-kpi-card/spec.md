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

共享统计卡 MUST 提供 `entry` 变体，用于仪表盘类「指标 + 进入」入口；该变体 SHALL 展示图标区、标题、主数值、描述文案，并在可导航时提供明确的进入控件或等价激活方式。

#### Scenario: Dashboard workflow card as entry variant

- **WHEN** 仪表盘以 `entry` 变体渲染「工作流」类统计入口，并提供导航目标
- **THEN** 卡片展示标题、主数值、描述与进入动作
- **AND** 激活进入动作（点击卡片或进入控件）SHALL 导航到对应模块路径

#### Scenario: Live indicator on entry card

- **WHEN** `entry` 变体启用 live 指示
- **THEN** 卡片展示可见的 live 状态标记
- **AND** 在 `prefers-reduced-motion: reduce` 下 live 标记 MUST NOT 依赖持续动画才能被理解

### Requirement: Optional doodle decorations

共享统计卡 SHALL 支持可选装饰（如图钉、胶带），装饰 MUST NOT 遮挡标题、数值或进入控件的可读性与可点区域。

#### Scenario: Decoration do not block interaction

- **WHEN** 卡片启用图钉或胶带装饰且为可点击 `entry` 卡
- **THEN** 用户仍可激活进入动作
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
