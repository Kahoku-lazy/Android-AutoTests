## MODIFIED Requirements

### Requirement: Shared KPI card uses doodle shell

系统 MUST 通过共享统计卡组件呈现指标，其默认外观 SHALL 采用 Hand-Drawn Doodle 卡壳：**浅色 accent 实线描边（与阴影第一层同色：color-mix(in srgb, var(--kpi-accent) 42%, var(--paper))）**、近直角圆角、**仅在右下的浅色分层硬阴影**（同色相三层、逐层变浅，偏移 4/8/12px、模糊半径 0）；SHALL NOT 再使用实线细边 + 大圆角 + 模糊 elevation 作为该组件的默认样式，SHALL NOT 使用墨色虚线描边，SHALL NOT 使用单层高饱和硬阴影。

#### Scenario: Default kpi card renders doodle shell

- **WHEN** 页面渲染共享统计卡且未指定 `entry` 变体
- **THEN** 卡片可见浅色 accent 实线边框（与右下阴影同色相）与近直角圆角，右下有三层由深到浅的同色相硬阴影，上方与左侧无阴影
- **AND** accent 色来自传入的模块色（或等价 CSS 变量）

#### Scenario: Existing kpi props remain compatible

- **WHEN** 既有调用方仅传入 label、value、color、shape，并可选监听 click
- **THEN** 卡片仍展示标签与数值，shape 装饰仍可区分卡片
- **AND** 点击时仍触发原有 click 行为

### Requirement: Reduced motion and keyboard access

可点击的共享统计卡 MUST 支持键盘激活；在用户启用减少动效时，卡片 MUST NOT 依赖倾斜或位移动画来传达可交互性。

#### Scenario: Keyboard activation for clickable card

- **WHEN** 可点击统计卡获得焦点且用户按下 Enter 或 Space
- **THEN** 系统执行与主键击相同的导航或 click 行为

#### Scenario: Reduced motion disables tilt animation

- **WHEN** 用户环境为 `prefers-reduced-motion: reduce`
- **THEN** 卡片悬停/入场 MUST NOT 播放依赖旋转或位移动效的反馈
- **AND** 卡片仍保持 doodle 静态壳样式（实线描边 + 右下浅色分层阴影）

### Requirement: Entry card primary value matches accent shadow

`entry` 变体的主数值色 MUST 与该卡 accent 色一致（同一 CSS 自定义属性来源；该 accent 同时用于描边）。系统 SHALL NOT 把 `entry` 主数值固定为墨色。默认 `kpi` 变体的主数值 MUST 仍为墨色。标题、描述、趋势文案与图标描边 MUST NOT 改用 accent。薄包装组件 SHALL NOT 用更高优先级规则把 `entry` 主数值重新锁成墨色。

#### Scenario: Dashboard entry value uses the same color as the hard shadow

- **WHEN** 仪表盘以 `entry` 变体渲染统计入口卡
- **THEN** 居中主数值的颜色与该卡描边所用 accent 色一致
- **AND** 标题、描述与趋势小字仍为墨色或既有次要/成功色，不随 accent 改变

#### Scenario: Compact kpi variant value stays ink

- **WHEN** 页面以默认 `kpi` 变体渲染共享统计卡
- **THEN** 主数值为 accent 同色系渐变，标题为墨色
- **AND** 卡片描边与阴影同色（accent 42% 混纸白），accent 仍用于主数值与图钉
