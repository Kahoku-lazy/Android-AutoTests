## Context

- EP 条纹规则：`.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell { background: var(--el-fill-color-lighter) }` —— 特异性 (0,4,2)、**无** `!important`。
- 全局规则：`style.css` 的 `.el-table td { background: var(--app-bg-card) !important }` —— 特异性 (0,1,1) 带 `!important`，**胜出**。
- `tokens.css` 已为行选中态登记 `--comp-table-row-accent` / `--comp-table-row-selected-bg`（变更 1），本变更沿用同一命名与派生方式。
- EP 的 `--el-fill-color-lighter` 是冷灰 `#fafafa`，且 `tokens.css` 未映射它 —— 即便条纹能渲染也会偏离暖色纸面。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- 传 `striped` 的表格出现可感知斑马纹
- 条纹底色取自登记令牌（暖色族）
- 选中态仍优先于条纹

**Non-Goals**

- 不改 `AppTable` 的 `striped → stripe` 映射
- 不改全局 `.el-table td` 的 `!important`（变更 1 已论证去掉它会波及 20 个页面）
- 不改各页面是否传 `striped`（`report-generator/index.vue` 显式传 `false`，保持）

## Decisions

**D1 把条纹画在 `> td.el-table__cell` 上并带 `!important`**
理由：与变更 1 的选中行完全同一手法；全局 td 底色带 `!important`，任何画在 `tr` 上的条纹都必被遮盖。
备选：去掉全局 td 底色的 `!important` —— 否决（变更 1 已评估，回归面 20 个页面）。

**D2 用 `color-mix` 从暖灰令牌派生条纹底色**
理由：条纹需要"可感知但柔和"，而登记令牌里没有合适的中性浅底（`--color-lime-94` 在白底上几乎不可见、`--color-orange-76` 过重）；用 `color-mix(in srgb, var(--color-orange-76) 25%, var(--app-bg-card))` 可得到暖色浅条纹，且色源仍是登记原子。

**D3 规则顺序置于选中规则之前**
理由：两者特异性相同，靠来源顺序决定优先级；选中态必须赢。

## Risks / Trade-offs

- [`25%` 的暖灰可能过重或过轻] → 这是可单点调节的令牌值；tasks 含"两行底色差异可感知"的断言与目视建议
- [规则若同时命中未请求条纹的表格会误加条纹] → 选择器限定 `.el-table--striped` 祖先，与 EP 一致

## Migration Plan

1. 先登记令牌，再加共享规则，然后断言
2. 回滚策略：纯样式改动，回滚即 `git revert`；无数据迁移

## Open Questions

（无）