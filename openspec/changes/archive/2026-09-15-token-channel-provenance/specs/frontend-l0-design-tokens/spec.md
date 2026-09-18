## ADDED Requirements

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