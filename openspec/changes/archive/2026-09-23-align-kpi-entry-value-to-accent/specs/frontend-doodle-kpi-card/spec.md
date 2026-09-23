## ADDED Requirements

### Requirement: Entry card primary value matches accent shadow

`entry` 变体的主数值色 MUST 与该卡硬偏移阴影所用 accent 色一致（同一 CSS 自定义属性来源）。系统 SHALL NOT 把 `entry` 主数值固定为墨色。默认 `kpi` 变体的主数值 MUST 仍为墨色。标题、描述、趋势文案与图标描边 MUST NOT 改用 accent。薄包装组件 SHALL NOT 用更高优先级规则把 `entry` 主数值重新锁成墨色。

#### Scenario: Dashboard entry value uses the same color as the hard shadow

- **WHEN** 仪表盘以 `entry` 变体渲染统计入口卡
- **THEN** 居中主数值的颜色与该卡硬偏移阴影色一致
- **AND** 标题、描述与趋势小字仍为墨色或既有次要/成功色，不随 accent 改变

#### Scenario: Compact kpi variant value stays ink

- **WHEN** 页面以默认 `kpi` 变体渲染共享统计卡
- **THEN** 主数值仍为墨色
- **AND** 硬偏移阴影仍使用传入的模块 accent
