## MODIFIED Requirements

### Requirement: Every color a module consumes has a registry location

模块样式（`modules/**/*.vue` 的 `<style>`、`modules/**/*.css`）中出现的每个色值 MUST 有登记处：或为 `shared/styles/tokens.css` 的全局令牌，或为承载消费元素的作用域内具名自定义属性。消费规则 MUST NOT 出现未登记的裸字面量。**画布绘制色**（ECharts / canvas）MAY 保留字面量，但 MUST 集中在该模块的图表色表（如 `constants.ts`）中声明，SHALL NOT 散落在组件样式或模板内联样式里。模块 MUST NOT 借用其它模块的私有令牌家族。

#### Scenario: Module-private palette is declared at its consumer scope

- **WHEN** 某模块需要一组仅本模块使用的色值（如 `case-manager` 的 7 色测试类型标签）
- **THEN** 每个色值在同一组件根类或消费元素自身的具名自定义属性中声明一次
- **AND** 消费规则只引用变量，不再出现裸字面量

#### Scenario: Chart and canvas colors are centralized

- **WHEN** 检查图表系列色与 canvas 绘制色
- **THEN** 它们集中在该模块的图表色表常量中（如 `report-generator/constants.ts` 的 `CHART_COLORS`）
- **AND** 组件样式与模板内联样式不再各自写字面量

#### Scenario: Cross-module token borrowing is removed

- **WHEN** 检索模块样式引用其它模块的私有家族令牌（如 `device-pool` 使用 `var(--ai-*)`）
- **THEN** 命中为 0，改用全局令牌（本轮改为 `--app-bg-subtle`）

#### Scenario: Deprecated aliases and the legacy family are retired

- **WHEN** 检索 `@deprecated` 别名（`--app-ink` / `--app-ink-muted` / `--app-green` / `--app-blue` / `--app-accent-*`）与 `--doodle-*` 家族
- **THEN** 两者的声明与用法均归零，已映射到现役令牌

### Requirement: 共享皮肤不依赖模块作用域令牌

共享样式（`shared/styles/**` 及 `shared/components/**` 内的样式）SHALL NOT 消费模块作用域令牌（即声明在 `.ai-workbench` / `.case-workbench` 等模块页面根类内的令牌）。共享皮肤在多个模块的页根上同时生效，消费模块令牌会使其在未声明该令牌的页根上**静默失效**，造成同一共享组件跨模块外观不一致。共享皮肤所需的外观值 MUST 取自 T0 主 token 或声明在 `:root` 上的共享组件令牌（`--comp-*`）。模块令牌文件内 SHALL NOT 重复声明同一令牌。

#### Scenario: Workbench shell does not consume module tokens

- **WHEN** 检查 `shared/styles/workbench-theme.css` 对 `.wb-shell` 的声明
- **THEN** 其 `font-family` / `color` 取自 `--app-font` / `--ink` 等共享或主 token
- **AND** 不再出现只声明在单个模块页根内的 `--ac-font` / `--ac-ink` 一类令牌

#### Scenario: Shared card pin shadow resolves in every module

- **WHEN** 在 dashboard、report-generator 或 ai-assistant 的任一页面上渲染 `AppCard` 的图钉（`.ac-card__pin`）
- **THEN** 该图钉的计算 `box-shadow` 非 `none`，且色源取自 `:root` 上的共享组件令牌
- **AND** 不再出现同一共享组件在不同模块间硬阴影有无不一致的差异

#### Scenario: Module token is declared once

<!-- 场景名沿自变更前：--ac-accent 的唯一声明处 modules/workflow/tokens.css 已随页面流模块删除，本场景改为守住「零残留声明」 -->

- **WHEN** 检索 `--ac-accent` 的声明
- **THEN** 命中数为 `0`（原唯一声明处 `modules/workflow/tokens.css` 已随模块删除）
- **AND** 不存在任何模块令牌文件重复声明同一令牌的情况

#### Scenario: Zero-consumer tokens left by the fix are removed

- **WHEN** 检索 `--ac-font` / `--ac-ink` / `--ac-pin-shadow`
- **THEN** 三者的声明与消费命中数均为 `0`
