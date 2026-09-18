## ADDED Requirements

### Requirement: Element Plus 原子被覆盖到主题内且交互文本可读

应用使用的 Element Plus 原子 MUST 由主题覆盖到 Doodle Craft 语言内：其几何 MUST NOT 回落到 EP 默认几何，其配色 MUST NOT 回落到 EP 默认调色板。交互文本（按钮文字、分段控件选中态、表单校验提示、错误面文字）与自身背景的计算对比度 MUST 不低于 **4.5:1**。EP 变量覆盖 MUST 引用主 token 原子（沿用「Element Plus 覆盖引用主 token 原子」）。

#### Scenario: Danger buttons are readable in both solid and plain variants

- **WHEN** 在浏览器测量 `type="danger"` 与 `type="danger" plain` 按钮的文字色与背景色并计算对比度
- **THEN** 两者的对比度均不低于 `4.5:1`
- **AND** 不再出现"白字压浅桃底"或"浅桃字压近白底"的组合

#### Scenario: Form validation error text is readable

- **WHEN** 触发表单校验失败并测量错误提示文字与其背景
- **THEN** 错误文字取自已登记的深红令牌，对比度不低于 `4.5:1`

#### Scenario: Segmented control keeps doodle geometry and a readable active state

- **WHEN** 打开任何使用 `el-radio-button` 的分段控件（如 `/elements` 的页面元素表筛选器）
- **THEN** 每个分段的计算圆角非零且取自已登记的 `--app-radius-*`，不因 EP 变量的多值组合而在 computed-value 阶段失效回落到 0
- **AND** 选中态文字与选中底色的对比度不低于 `4.5:1`，且与项目其他分段控件（`AppTabs`）同口径

#### Scenario: Skeleton and fill surfaces stay on the warm paper

- **WHEN** 渲染 `el-skeleton` 或任何使用 `--el-fill-color` 的占位与浅底
- **THEN** 其计算底色取自已登记的暖色族令牌
- **AND** 不再出现 EP 默认的冷灰 `#f0f2f5`

#### Scenario: Switch uses themed geometry and on/off colors

- **WHEN** 渲染 `el-switch`
- **THEN** 其轨道圆角取自已登记的 `--app-radius-*`
- **AND** 开态底色取自成功色令牌、关态底色取自离线灰令牌

#### Scenario: Error surfaces use the registered red family

- **WHEN** 渲染 `el-alert type="error"` 或 `el-message--error`
- **THEN** 其配色取自 `tokens.css` 已登记的红色原子，`--el-color-error*` 不再是 EP 默认的 `#f56c6c` / `#fef0f0`

#### Scenario: EP overrides still carry no literals

- **WHEN** 静态校验扫描主题文件的 `--el-*` 声明（对应 `npm run lint:styles`）
- **THEN** 其值 MUST 全部为 `var()` 引用，字面量命中为 `0`