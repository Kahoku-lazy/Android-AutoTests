## MODIFIED Requirements

### Requirement: Tables draw no visible grid lines

表格纸面 MUST NOT 呈现可见的行网格线与列网格线：模块色 SHALL NOT 用于行分隔线或列分隔线；系统 SHALL NOT 出现「以白色或近白色令牌（如 `--app-border-light`、`--color-white`）作为可见边框色」的声明。确需保留 1px 占位时 MUST 写作 `transparent` 并注明意图。表头排版 MUST 由全局与共享皮肤唯一定义：字号 **16px**（`--app-size-md`）、单行不折（`nowrap` 落在 `th .cell`）；字重与大小写变换沿用共享皮肤既有定义。模块 SHALL NOT 覆写表头字号。

#### Scenario: No module-specific separators

- **WHEN** 打开 `/devices` 表格视图与 `/reports` 列表
- **THEN** 两者都不出现彩色行分隔线或列分隔线
- **AND** 表格观感差异仅来自表纸强调色（`--c-device` / `--c-report`）与状态标识

#### Scenario: Header typography is single-sourced

- **WHEN** 比较 `/devices`、`/bugs`、`/reports` 与 `/cases` 的表格表头计算样式
- **THEN** 字号一致为 16px，字重与大小写变换一致
- **AND** 每个表头单行显示，不因字号变化折行
- **AND** 不存在模块私有的表头字号覆盖（设备页与 BUG 页的旧覆写已删除）

#### Scenario: White is never a visible border color

- **WHEN** 检索全仓表格样式中的边框色声明
- **THEN** 不存在以 `--app-border-light` 或 `--color-white` 作为可见行线/列线颜色的声明
- **AND** 保留占位的声明写作 `transparent` 并带意图注释
