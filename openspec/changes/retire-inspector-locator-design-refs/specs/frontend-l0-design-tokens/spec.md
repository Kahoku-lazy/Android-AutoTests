## MODIFIED Requirements

### Requirement: Module styles consume registered design tokens

模块样式（`modules/**/*.vue` 的 `<style>` 与 `modules/**/*.css`）中的**语义色与状态色** MUST 取 `shared/styles/tokens.css` 已登记的令牌（`--c-*` / `--app-status-*` / `--ink` / `--paper` / `--app-bg-*` / `--app-text-*`），MUST NOT 直写字面量。**文本字号** MUST 取 `--app-size-*` 刻度且 MUST NOT 低于 12px（图形/展示级字号例外见 `frontend/AGENTS.md` 硬性规范 §1.14）。Element Plus 默认调色板（如 `#409eff`）MUST NOT 被当作模块色。**画布绘制色**（ECharts 系列色 / canvas 绘制色，同既有 ECharts 例外）与**数据编码型分类色板**（分类标签色）MAY 保留字面色相；其中分类色板每个色相 MUST 在该文件的具名局部自定义属性中声明一次，SHALL NOT 在规则里重复散落同一字面量。

#### Scenario: Semantic and state colors come from tokens

- **WHEN** 静态检索模块样式中危险 / 成功 / 通过 / 失败 / hover 态等语义色的字面量
- **THEN** 这些位置引用 `--app-status-*` 等令牌，不再出现字面量（canvas 绘制色与图表系列色除外，见需求正文例外）
- **AND** 本轮收敛：`ai-assistant/KnowledgeBase.vue` 的 hover 危险字面量、`case-manager` 两个文件的白底与危险字面量、`report-generator` 两个文件的通过 / 失败字面量

#### Scenario: Element Plus default palette is not used as a module color

- **WHEN** 检索模块样式中的 Element Plus 默认色（`#409eff` / `#67c23a` / `#f56c6c` / `#e6a23c`）
- **THEN** 命中为 0，改用该模块的 `--c-*` 模块色或 `--app-status-*` 状态色

#### Scenario: Text size respects the 12px floor

- **WHEN** 静态检索模块样式中 `font-size` 的 px 字面量
- **THEN** 不存在低于 12px 的文本字号，其余字面量仅限图形 / 展示级例外
- **AND** `dashboard/DashboardView.style.css` 的 `.subhead__tag` 由 `10px` 改为 `var(--app-size-xs)`

#### Scenario: Literal values registered as tokens are replaced by the token

- **WHEN** 某处字面量色值与 `tokens.css` 已登记令牌的值等价
- **THEN** 该处引用令牌而非字面量
- **AND** 本轮收敛 `report-generator` 的 `#a03030` → `--app-status-danger-text`

#### Scenario: Categorical palettes are declared once

- **WHEN** 检查数据编码型分类色板的使用方式（`case-manager` 的 7 色测试类型标签）
- **THEN** 每个色相只在具名局部自定义属性中声明一次，消费规则里不再出现裸字面量
- **AND** 色相与分类语义保持不变（不压缩为状态色）

### Requirement: 阴影规格扁平且不含模糊投影

前端样式中的阴影（`box-shadow` / `text-shadow`，**含经自定义属性间接声明**的阴影值）MUST 采用扁平硬偏移形式：模糊半径（长度序列的第三个值）MUST 为 `0`。系统 SHALL NOT 使用带模糊半径的投影表达层次或"悬浮感"，也 SHALL NOT 使用外发光（形如 `0 0 <blur>`）作为强调手段。阴影的偏移量与色源 SHOULD 取 `tokens.css` 已登记的 `--app-shadow-*` / `--comp-*-shadow*` 令牌；模块确需自定义色源时，该色源仍 MUST 是已登记的颜色原子或引用它的局部自定义属性。

#### Scenario: No blurred shadow remains in the source tree

- **WHEN** 静态检索 `frontend/src` 下全部 `.vue` / `.css` 的阴影声明（包括自定义属性值内嵌的阴影）并解析其模糊半径
- **THEN** 模糊半径大于 `0` 的命中数为 `0`

#### Scenario: Floating surfaces use flat hard shadow

- **WHEN** 打开仍存在的等价页面
- **THEN** 这些表面的阴影为零模糊硬偏移（无光晕、无渐变过渡的柔影）
- **AND** 浮层仍与下层纸面可区分（描边或硬偏移影至少其一可见）

#### Scenario: Indirectly declared shadows obey the same rule

- **WHEN** 某组件通过自定义属性（例如 `--avatar-shadow`）间接声明阴影并在消费处使用 `box-shadow: var(--avatar-shadow)`
- **THEN** 该自定义属性的值同样满足零模糊约束
- **AND** 收敛后不保留零消费方的阴影自定义属性

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

- **WHEN** 打开仍存在的等价页面
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
