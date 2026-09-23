# frontend-l0-design-tokens Specification

## Purpose
TBD - created by archiving change converge-module-theme-tokens. Update Purpose after archive.

## Requirements

### Requirement: Module styles consume registered design tokens

模块样式（`modules/**/*.vue` 的 `<style>` 与 `modules/**/*.css`）中的**语义色与状态色** MUST 取 `shared/styles/tokens.css` 已登记的令牌（`--c-*` / `--app-status-*` / `--ink` / `--paper` / `--app-bg-*` / `--app-text-*`），MUST NOT 直写字面量。**文本字号** MUST 取 `--app-size-*` 刻度且 MUST NOT 低于 12px（图形/展示级字号例外见 `frontend/AGENTS.md` 硬性规范 §1.14）。Element Plus 默认调色板（如 `#409eff`）MUST NOT 被当作模块色。**画布绘制色**（ECharts 系列色 / canvas 绘制色，同既有 ECharts 例外）与**数据编码型分类色板**（分类标签色）MAY 保留字面色相；其中分类色板每个色相 MUST 在该文件的具名局部自定义属性中声明一次，SHALL NOT 在规则里重复散落同一字面量。

#### Scenario: Semantic and state colors come from tokens

- **WHEN** 静态检索模块样式中危险 / 成功 / 通过 / 失败 / hover 态等语义色的字面量
- **THEN** 这些位置引用 `--app-status-*` 等令牌，不再出现字面量（canvas 绘制色与图表系列色除外，见需求正文例外）
- **AND** 本轮收敛：`ai-assistant/KnowledgeBase.vue` 的 hover 危险字面量、`case-manager` 两个文件的白底与危险字面量、`report-generator` 两个文件的通过 / 失败字面量

#### Scenario: Element Plus default palette is not used as a module color

- **WHEN** 检索模块样式中的 Element Plus 默认色（`#409eff` / `#67c23a` / `#f56c6c` / `#e6a23c`）
- **THEN** 命中为 0，改用该模块的 `--c-*` 模块色或 `--app-status-*` 状态色
- **AND** 本轮收敛 `device-inspector/components/PageElementsPanel.vue` 的 dump / OCR 徽标底色

#### Scenario: Text size respects the 12px floor

- **WHEN** 静态检索模块样式中 `font-size` 的 px 字面量
- **THEN** 不存在低于 12px 的文本字号，其余字面量仅限图形 / 展示级例外
- **AND** `dashboard/DashboardView.style.css` 的 `.subhead__tag` 由 `10px` 改为 `var(--app-size-xs)`

#### Scenario: Literal values registered as tokens are replaced by the token

- **WHEN** 某处字面量色值与 `tokens.css` 已登记令牌的值等价
- **THEN** 该处引用令牌而非字面量
- **AND** 本轮收敛 `report-generator` 的 `#a03030` → `--app-status-danger-text`、`device-inspector` 的 `#a78bfa` → `--c-element`

#### Scenario: Categorical palettes are declared once

- **WHEN** 检查数据编码型分类色板的使用方式（`case-manager` 的 7 色测试类型标签）
- **THEN** 每个色相只在具名局部自定义属性中声明一次，消费规则里不再出现裸字面量
- **AND** 色相与分类语义保持不变（不压缩为状态色）

### Requirement: Every color a module consumes has a registry location

模块样式（`modules/**/*.vue` 的 `<style>`、`modules/**/*.css`）中出现的每个色值 MUST 有登记处：或为 `shared/styles/tokens.css` 的全局令牌，或为承载消费元素的作用域内具名自定义属性。消费规则 MUST NOT 出现未登记的裸字面量。**画布绘制色**（ECharts / canvas）MAY 保留字面量，但 MUST 集中在该模块的图表色表（如 `constants.ts`）中声明，SHALL NOT 散落在组件样式或模板内联样式里。模块 MUST NOT 借用其它模块的私有令牌家族。

#### Scenario: Module-private palette is declared at its consumer scope

- **WHEN** 某模块需要一组仅本模块使用的色值（如 `case-manager` 的 7 色测试类型标签）
- **THEN** 每个色值在同一组件根类或消费元素自身的具名自定义属性中声明一次
- **AND** 消费规则只引用变量，不再出现裸字面量

#### Scenario: Chart and canvas colors are centralized

- **WHEN** 检查图表系列色与 canvas 绘制色
- **THEN** 它们集中在该模块的图表色表常量中（`report-generator/constants.ts` 的 `CHART_COLORS` · workflow 节点色表）
- **AND** 组件样式与模板内联样式不再各自写字面量

#### Scenario: Cross-module token borrowing is removed

- **WHEN** 检索模块样式引用其它模块的私有家族令牌（如 `device-pool` 使用 `var(--ai-*)`）
- **THEN** 命中为 0，改用全局令牌（本轮改为 `--app-bg-subtle`）

#### Scenario: Deprecated aliases and the legacy family are retired

- **WHEN** 检索 `@deprecated` 别名（`--app-ink` / `--app-ink-muted` / `--app-green` / `--app-blue` / `--app-accent-*`）与 `--doodle-*` 家族
- **THEN** 两者的声明与用法均归零，已映射到现役令牌

### Requirement: Module token families are scoped to the module root

模块私有令牌家族 MUST NOT 声明在 `:root`；MUST 声明在该模块页面根类的作用域内（如 `.ai-workbench`、`.case-workbench`）。仅当消费点确实会被 Teleport 到 `body`【如显式 `append-to-body` 的弹层】时，MAY 退化为全局声明，且 MUST 在声明处注释说明原因。

#### Scenario: Root scope carries no module-private variables

- **WHEN** 检索 `tokens.css` 的 `:root` 块内的模块前缀变量（`--ai-*` / `--case-*`）
- **THEN** 命中为 0，家族已迁入对应模块作用域（`.ai-workbench` / `.case-workbench`）
- **AND** 模块作用域块内可见完整家族声明

#### Scenario: Scoped family still reaches in-place overlays

- **WHEN** 模块内的 `el-dialog` / `el-drawer` 使用该家族令牌
- **THEN** 因 EP 默认不 Teleport（`appendToBody` 默认 false）弹层原地渲染，作用域变量仍可达
- **AND** 若某弹层显式开启 Teleport，则按需求正文的逃逸口处理并在声明处注释

### Requirement: 主 token 是颜色与规格的唯一登记处
共享层主 token SHALL 以按颜色命名的原子登记全部字面量色值，并 SHALL 是字面量色值的唯一声明位置；其他任何位置（模块层、组件层、Element Plus 覆盖）MUST 通过 `var()` 引用。

#### Scenario: 新增色值先登记原子
- **WHEN** 任一模块或组件需要一个主 token 中尚不存在的色值
- **THEN** 该色值 MUST 先作为颜色原子登记于主 token，消费处 MUST 以 `var()` 引用该原子

#### Scenario: 同值不重复声明
- **WHEN** 对主 token 运行静态校验
- **THEN** 同一色值的字面量声明 MUST 恰好出现一次，其余引用 MUST 为 `var()`

### Requirement: 主 token 命名只描述颜色与规格
主 token 的颜色、排版、基础量三档声明名 MUST 仅由颜色或规格构成，SHALL NOT 含使用场景名或模块名；模块用途 MUST 在模块层以 `var()` 组合表达。

#### Scenario: 新增原子命名合法性
- **WHEN** 对主 token 运行静态校验
- **THEN** 任何新增原子名 MUST 遵循颜色（`--color-<色相>-<明度>`）或规格（`--font*` / `--space-*` / `--radius-*` / `--shadow-*` / `--duration-*` / `--ease` / `--size-*`）命名，且 MUST NOT 含模块前缀（`--ai-` / `--case-` / `--rg-` / `--di-` / `--wf-` / `--views-`）

#### Scenario: 场景语义留在模块层
- **WHEN** 某模块需要「标签底色」这类场景语义
- **THEN** 该语义 MUST 声明在模块层并取值于主 token 原子，SHALL NOT 在主 token 中新增场景名声明

### Requirement: 通用组件配色独立成档
共享层 SHALL 为跨模块复用的通用组件提供配色档，声明名 MUST 采用 `--comp-<组件>-<场景>` 形式，且 SHALL NOT 含模块名。

#### Scenario: 通用组件令牌落档
- **WHEN** `shared/components/**` 中的组件需要模块无关的场景配色
- **THEN** 该配色 MUST 以 `--comp-<组件>-<场景>` 声明，其值 MUST 引用颜色原子

### Requirement: Element Plus 覆盖引用主 token 原子
主题对 Element Plus 变量的覆盖 MUST 引用主 token 原子，SHALL NOT 直接书写字面量色值。

#### Scenario: EP 覆盖不再直写字面量
- **WHEN** 静态校验扫描主题文件的 `--el-*` 声明
- **THEN** 其值 MUST 全部为 `var()` 引用，字面量命中 MUST 为 0

### Requirement: 模块令牌按模块落文件
每个拥有模块级场景令牌的模块 SHALL 在本模块目录下提供 `tokens.css`，其内容 SHALL 覆盖该模块全部模块级场景令牌；共享层 SHALL NOT 承载模块级场景令牌。

#### Scenario: 模块级令牌的落点
- **WHEN** 某模块需要跨组件复用的场景令牌（如标签底色、抽屉描边）
- **THEN** 该令牌 MUST 声明在 `modules/<模块>/tokens.css`，且 MUST NOT 继续留在 `shared/styles/**`

#### Scenario: 迁移后共享层无模块令牌
- **WHEN** 静态校验扫描 `shared/styles/tokens.css`
- **THEN** 其中 MUST NOT 存在 `--ai-*` / `--case-*` 等模块家族声明

### Requirement: 模块令牌值引用主 token
模块令牌的值 MUST 引用 T0 主 token 原子；模块令牌文件内 SHALL NOT 出现字面量色值。

#### Scenario: 模块令牌无字面量
- **WHEN** 静态校验扫描 `modules/*/tokens.css`
- **THEN** 任何 `--name: <字面量色值>` 的命中 MUST 为 0，值 MUST 形如 `var(--color-*)`

#### Scenario: 组件级载体同样引用原子
- **WHEN** 某组件在自身根类声明只被它消费的场景令牌
- **THEN** 其值 MUST 引用 T0 主 token 原子，SHALL NOT 写字面量色值

### Requirement: 模块令牌作用域保持在模块页面根类
模块令牌 SHALL 声明在该模块页面根类的作用域内，以模块页面根类为选择器；SHALL NOT 提升为 `:root` 全局声明。

#### Scenario: 作用域不因文件迁移而改变
- **WHEN** 模块令牌从共享文件迁至模块文件
- **THEN** 其选择器 MUST 保持为原模块页面根类（如 `.ai-workbench`），MUST NOT 改为 `:root`

#### Scenario: Teleport 目标的例外
- **WHEN** 某模块的浮层显式 Teleport 到 `body`
- **THEN** 该浮层所需令牌 MUST 声明在被传送元素自身根类上，并在声明处注释原因

### Requirement: 无引用样式文件不得留在源码树
源码树 SHALL NOT 保留没有任何引用的样式文件（既无路径引用、也无变量消费）。识别出的死样式文件 MUST 移出源码树或删除，并记录恢复方式。

#### Scenario: 死样式文件的处置
- **WHEN** 某样式文件在全仓既无 `@import` / `src` 路径引用，其声明的自定义属性也无任何消费方
- **THEN** 该文件 MUST 移出 `frontend/src`（或删除），且处置方式 MUST 可恢复

### Requirement: 共享样式目录命名唯一
跨模块共享样式 SHALL 只位于 `shared/styles/` 与 `shared/components/`；其它目录 SHALL NOT 复用 `shared` 这一级命名空间。

#### Scenario: 视图层局部样式不占用 shared 命名
- **WHEN** 视图层需要归集自身的局部样式
- **THEN** 其目录 MUST NOT 命名为 `shared`（如改为 `views/styles/`），避免与平台 `shared/` 混淆

#### Scenario: 目录改名后引用同步
- **WHEN** 归集目录改名
- **THEN** 所有引用该目录的 `@import` / `src` 路径 MUST 同步更新，且旧路径命中 MUST 为 0

### Requirement: 非样式表载体按边界溯源令牌
位于 `<style>` 块之外的外观值引用（模板内联 `style`、SVG 元素属性、组件 prop、脚本字符串）SHALL 按调用点所在边界引用令牌：模块内 MUST 引用该模块 T1 场景令牌，共享层 MUST 引用 T0 主 token 原子或通用组件令牌。

**例外（跨模块通用值）**：状态色（`--app-status-*` / `--app-error` 等）、文本层级（`--app-text-*`）、字号（`--app-size-*`）、基础量（`--app-space-*` 等）与模块色（`--c-*`）是跨模块通用的语义与刻度，任何边界 MAY 直取 T0，MUST NOT 为每个模块再包一层同名场景令牌。

#### Scenario: 模块内载体引用本模块令牌
- **WHEN** `modules/<模块>/**` 或 `views/**` 中的模板属性或脚本字符串需要一个**模块专属**外观值（如本模块的场景底色、连接指示色）
- **THEN** 它 MUST 引用该边界的 T1 令牌；若 T1 无对应场景 MUST 先新增（其值引用 T0），SHALL NOT 直接引用其它模块的 T1

#### Scenario: 通用语义与刻度直取 T0
- **WHEN** 模块内载体需要的是跨模块通用的状态色 / 文本层级 / 字号 / 基础量 / 模块色
- **THEN** 它 MAY 直接引用 T0 的对应令牌（含 `--app-*` / `--c-*` 兼容别名），MUST NOT 在模块内新增仅作同值转写的场景令牌（如 `--ai-alias-danger-text: var(--color-red-40)`）

#### Scenario: 共享层载体引用主 token
- **WHEN** `shared/**` 中的组件（如 `AppCard` / `PaperDoodles`）需要一个外观值
- **THEN** 它 MUST 引用 T0 颜色原子或 `--comp-*` 通用组件令牌，SHALL NOT 引用任何模块 T1

### Requirement: 脚本侧令牌字符串不得携带字面量兜底
脚本中作为字符串传递的令牌引用 MUST NOT 包含字面量兜底（`var(--x, #色值)`）；被引用令牌 MUST 在主 token 或本模块令牌中存在。

#### Scenario: 去掉兜底字面量
- **WHEN** 脚本或模板中出现 `var(--<令牌>, <字面量色值>)`
- **THEN** 该字面量兜底 MUST 被移除（前提：被引用令牌已存在），静态校验命中 MUST 为 0

### Requirement: 颜色原子以调色板为准且只降不增
T0 主 token 的颜色原子 SHALL 收敛为一套经感知聚类（CIE76 ΔE ≤ 8）确定的调色板：每个原子 MUST 属于该调色板，原子总数 MUST NOT 超过登记上限，命名 MUST 形如 `--color-<色相>-<明度 2 位>[-s<饱和>][-a<alpha 2 位>]`，SHALL NOT 再出现序号兜底名（`-2`…`-9`）。透明度 SHALL 只取调色板登记的 alpha 档位。调色板之外的色值 MUST NOT 进入 T0。

#### Scenario: 新颜色需求先复用调色板
- **WHEN** 开发需要一个新的颜色或透明度
- **THEN** MUST 先复用调色板内最接近的原子（ΔE ≤ 8）；确需新增 MUST 先修订调色板并同步上限，SHALL NOT 直接往 tokens.css 追加原子

#### Scenario: 门禁拦截调色板外原子
- **WHEN** 静态校验扫描 `shared/styles/tokens.css`
- **THEN** 颜色原子总数 MUST ≤ 登记上限、每个原子名 MUST 命中调色板白名单、且 SHALL NOT 命中序号兜底名模式；任一命中即 exit 非 0

### Requirement: 阴影规格扁平且不含模糊投影

前端样式中的阴影（`box-shadow` / `text-shadow`，**含经自定义属性间接声明**的阴影值）MUST 采用扁平硬偏移形式：模糊半径（长度序列的第三个值）MUST 为 `0`。系统 SHALL NOT 使用带模糊半径的投影表达层次或"悬浮感"，也 SHALL NOT 使用外发光（形如 `0 0 <blur>`）作为强调手段。阴影的偏移量与色源 SHOULD 取 `tokens.css` 已登记的 `--app-shadow-*` / `--comp-*-shadow*` 令牌；模块确需自定义色源时，该色源仍 MUST 是已登记的颜色原子或引用它的局部自定义属性。

#### Scenario: No blurred shadow remains in the source tree

- **WHEN** 静态检索 `frontend/src` 下全部 `.vue` / `.css` 的阴影声明（包括自定义属性值内嵌的阴影）并解析其模糊半径
- **THEN** 模糊半径大于 `0` 的命中数为 `0`
- **AND** 本轮收敛 `ai-assistant` 2 处、`device-inspector` 4 处、`workflow` 2 处

#### Scenario: Floating surfaces use flat hard shadow

- **WHEN** 打开设备检查器的截图面板与两个放大预览浮层，以及工作流的 API 节点与元素选择浮层
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

### Requirement: 共享皮肤不依赖模块作用域令牌

共享样式（`shared/styles/**` 及 `shared/components/**` 内的样式）SHALL NOT 消费模块作用域令牌（即声明在 `.ai-workbench` / `.case-workbench` / `.workflow-workbench` 等模块页面根类内的令牌）。共享皮肤在多个模块的页根上同时生效，消费模块令牌会使其在未声明该令牌的页根上**静默失效**，造成同一共享组件跨模块外观不一致。共享皮肤所需的外观值 MUST 取自 T0 主 token 或声明在 `:root` 上的共享组件令牌（`--comp-*`）。模块令牌文件内 SHALL NOT 重复声明同一令牌。

#### Scenario: Workbench shell does not consume module tokens

- **WHEN** 检查 `shared/styles/workbench-theme.css` 对 `.wb-shell` / `.workflow-workbench` 的声明
- **THEN** 其 `font-family` / `color` 取自 `--app-font` / `--ink` 等共享或主 token
- **AND** 不再出现只声明在单个模块页根内的 `--ac-font` / `--ac-ink` 一类令牌

#### Scenario: Shared card pin shadow resolves in every module

- **WHEN** 在 dashboard、report-generator 或 ai-assistant 的任一页面上渲染 `AppCard` 的图钉（`.ac-card__pin`）
- **THEN** 该图钉的计算 `box-shadow` 非 `none`，且色源取自 `:root` 上的共享组件令牌
- **AND** 不再出现"同一共享组件在 workflow 有硬阴影、在其他模块无阴影"的差异

#### Scenario: Module token is declared once

- **WHEN** 检查 `modules/workflow/tokens.css` 的 `--ac-accent`
- **THEN** 该令牌只声明一次，取值与模块色登记一致（工作流天蓝 `--c-workflow`）
- **AND** 不再存在后置声明静默改写其值的情况

#### Scenario: Zero-consumer tokens left by the fix are removed

- **WHEN** 检索 `--ac-font` / `--ac-ink` / `--ac-pin-shadow`
- **THEN** 三者的声明与消费命中数均为 `0`

### Requirement: 可见盒子的圆角取自不对称规格令牌

前端样式中**可见盒子**的圆角 MUST 取自 `tokens.css` 已登记的不对称规格令牌（`--app-radius-sm` / `--app-radius-md` / `--app-radius-lg` / `--app-radius-pill` / `--app-radius-table`，或其原子 `--radius-*`）。系统 SHALL NOT 在可见盒子上书写对称字面量（如 `999px` / `8px` / `12px`），也 SHALL NOT 书写与已登记令牌**等价**的多值展开形式（如 `4px 8px 4px 8px`）。登记例外：真实圆形的 `50%`、已登记 2px 纸角（`--comp-note-radius` / `--comp-sheet-radius` 分量）、`1px` / `3px` / `5px` 一类图形量、`0` 重置、方向性几何（如 `0 3px 3px 0`），以及登录页已登记的独立视觉。

#### Scenario: No equivalent multi-value expansion remains

- **WHEN** 静态检索 `frontend/src` 的 `border-radius` 字面量
- **THEN** 不再出现 `4px 8px 4px 8px` / `6px 10px 6px 10px` / `3px 6px 3px 6px` / `2px 6px 2px 4px`
- **AND** 这些位置引用对应的已登记令牌

#### Scenario: Pill shapes use the registered pill token

- **WHEN** 检索 `border-radius` 的 `999px`
- **THEN** 命中数为 `0`
- **AND** 原胶囊位置引用 `var(--app-radius-pill)`

#### Scenario: Visible boxes are asymmetric

- **WHEN** 逐项检查改动后的可见盒子计算圆角
- **THEN** 其四角不完全相等（不对称几何），或属于登记例外（`50%` / 2px 纸角 / 图形量 / 登录页）
- **AND** `--app-radius-pill` 的引用数由 0 变为正数

### Requirement: Stacking order comes from registered tokens

前端样式的 `z-index` SHOULD 取自 `tokens.css` 已登记的层叠令牌（`--z-*`）。系统 SHALL NOT 保留**悬空**的层叠令牌引用（引用了未声明的 `--z-*` / 模块 `--*-z-*` 令牌），因为该引用会在 computed-value 阶段失效并回落 `auto`，使层叠静默失效。单例值（未纳入档位的一次性层叠）MAY 保留字面量，但 MUST 在 `tokens.css` 的层叠令牌段登记其用途。

#### Scenario: No dangling stacking token remains

- **WHEN** 静态检索全仓 `.vue` / `.css` 的 `z-index` 声明与其引用的自定义属性
- **THEN** 每个被引用的层叠令牌都能在 `:root` 或对应模块 tokens.css 中找到声明
- **AND** `--case-z-context` 等此前悬空的令牌已声明且解析为预期层叠值

#### Scenario: Registered tiers match their previous literals

- **WHEN** 对比改动前后同值位置的 `z-index` 计算值
- **THEN** 取令牌的声明与其原字面量数值**逐一相同**
- **AND** 未纳入档位的单例值未被改动

#### Scenario: Module stacking tokens resolve inside their module

- **WHEN** 在 `case-manager` 的页面内渲染其上下文菜单
- **THEN** 该菜单的计算 `z-index` 为 `80`（不再为 `auto`）
- **AND** 与 `element-locator` 同类浮层的层级一致

### Requirement: 样式引用完整性门禁覆盖全部样式载体

引用完整性检查 SHALL 覆盖 `.css` 文件全文与 `.vue` 的 `<style>` 块，MUST NOT 因文件类型或样式块而豁免扫描。运行时注入的自定义属性名（`:style="{ '--x': v }"`、`style="--x: v"`）SHALL 按边界汇集后参与判定，以覆盖注入点与消费点分处同目录不同文件（如组件与它的 `X.style.css`）的情形。

#### Scenario: 样式表中的悬空引用被拦截

- **WHEN** `.css` 文件或 `.vue` 的 `<style>` 块引用了一个全仓无声明、且非运行时注入的令牌
- **THEN** 门禁 SHALL 以非零退出码阻断并报出文件与行号

#### Scenario: 样式表引用未声明的模块令牌被拦截

- **WHEN** 某边界的 `.css` 引用了仅声明于其他边界的模块令牌
- **THEN** 门禁 SHALL 判定为跨边界借用并阻断

#### Scenario: 组件与其同目录样式表之间的注入不被误判

- **WHEN** 某边界内的 `.vue` 通过 `:style` 注入自定义属性名，同边界的 `.css`（如 `X.style.css`）消费该名字
- **THEN** 该引用 SHALL 视为可解析，不产生悬空或跨边界告警

### Requirement: 几何尺度由门禁持续校验且只降不增

阴影模糊半径、圆角字面量与动效时长 SHALL 由门禁持续校验。`box-shadow` 的模糊半径 MUST 为 0；`border-radius` MUST 取自 `--app-radius-*`/`--radius-*`、图形量白名单或已登记的独立造型，等价四值展开（`A B A B`）MUST NOT 保留；`transition`/`animation` 简写中的时长 MUST 取自 `--app-duration-*`（已登记的循环装饰动画除外）。画布侧驼峰 `fontSize` 与已登记的图形量字面量 SHALL 以只降不增的上限保留。

#### Scenario: 模糊阴影被拦截

- **WHEN** 源码中出现模糊半径非 0 的 `box-shadow`
- **THEN** 门禁 SHALL 以非零退出码阻断

#### Scenario: 未登记圆角字面量被拦截

- **WHEN** 源码中出现既非令牌、又不在登记清单内的 `border-radius` 字面量
- **THEN** 门禁 SHALL 以非零退出码阻断

#### Scenario: 等价四值圆角被拦截

- **WHEN** `border-radius` 写成 `A B A B` 且与两值写法渲染完全等价
- **THEN** 门禁 SHALL 判定为冗余写法并阻断

#### Scenario: 刻度外动效时长被拦截

- **WHEN** `transition` 或 `animation` 简写中出现非 `var(--app-duration-*)` 的裸时长
- **THEN** 门禁 SHALL 以非零退出码阻断

#### Scenario: 画布字号存量只降不增

- **WHEN** ECharts / VueFlow 配置中的驼峰 `fontSize` 数量超过已登记上限
- **THEN** 门禁 SHALL 阻断

### Requirement: 字号刻度登记 48px 品牌展示档
`shared/styles/tokens.css` 的字号刻度 SHALL 在既有 6 档之外登记一档 48px 品牌展示级文本字号：T0 原子 `--font-size-3xl: 48px`，并 SHALL 提供等价别名 `--app-size-3xl`。该档 MUST 仅用于首屏品牌展示级文本（当前唯一消费点为登录页 Hero 标题），SHALL NOT 取代现有 6 档 UI 文本刻度。

#### Scenario: 48px 档以规格原子登记并提供别名
- **WHEN** 检索 `tokens.css` 的排版原子声明
- **THEN** 存在 `--font-size-3xl: 48px`，且别名区存在 `--app-size-3xl: var(--font-size-3xl)`
- **AND** 消费方以 `var()` 引用该档，样式文件中不存在 `font-size: 48px` 这类字面量

#### Scenario: 展示档不扩散到常规 UI 文本
- **WHEN** 检索样式文件中 `--app-size-3xl` 的使用位置
- **THEN** 命中仅出现在登录页 Hero 标题载体
