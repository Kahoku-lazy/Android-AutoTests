## MODIFIED Requirements

### Requirement: Tables draw no visible grid lines

表格纸面 MUST NOT 呈现可见的**列**网格线。行分隔线 MUST 为 `1px color-mix(in srgb, var(--ink) 8%, transparent)`，表头底线 MUST 为 `1px color-mix(in srgb, var(--ink) 14%, transparent)`；两者 MUST NOT 使用模块色（`--c-*`），也 MUST NOT 使用白色或近白色令牌（如 `--app-border-light`、`--color-white`）作为可见边框色。表头排版 MUST 由全局与共享皮肤唯一定义（`--app-size-xs` / `--app-font-weight-semibold` / `uppercase` / `--app-text-secondary` / `letter-spacing: 0.08em`）；模块 SHALL NOT 覆写表头字号或字重。

#### Scenario: No module-specific separators

- **WHEN** 打开 `/devices` 表格视图与 `/reports` 列表
- **THEN** 两者都不出现彩色行分隔线或列分隔线，行线为 ink 8% 中性色
- **AND** 表格观感差异仅来自表纸强调色（`--c-device` / `--c-report`）与状态标识

#### Scenario: Header typography is single-sourced

- **WHEN** 比较 `/devices`、`/reports` 与 `/cases` 的表格表头计算样式
- **THEN** 字号、字重、大小写变换与颜色一致（12px / 600 / uppercase / 次要色）
- **AND** 不存在模块私有的表头字号或字重覆盖

#### Scenario: White is never a visible border color

- **WHEN** 检索全仓表格样式中的边框色声明
- **THEN** 不存在以 `--app-border-light` 或 `--color-white` 作为可见行线/列线颜色的声明
- **AND** 行线与表头底线只使用 ink 系 `color-mix` 值
