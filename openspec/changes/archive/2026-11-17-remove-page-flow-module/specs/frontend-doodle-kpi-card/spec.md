## MODIFIED Requirements

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
