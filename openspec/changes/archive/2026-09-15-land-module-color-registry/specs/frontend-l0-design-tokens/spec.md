## ADDED Requirements

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
