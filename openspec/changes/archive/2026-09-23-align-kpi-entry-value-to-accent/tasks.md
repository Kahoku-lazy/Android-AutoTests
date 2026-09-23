## 1. 共享入口卡数值色

- [x] 1.1 将 `KpiCard.vue` 中 `entry` 主数值规则改为 `color: var(--kpi-accent)`，选择器限定 `.kpi-card--entry`（含 `.kpi-card__value` 与 `.kpi-card__stat :deep(strong)`）；验证：文件内 `.kpi-card--kpi .kpi-card__value` 仍为 `var(--ink)`，`entry` 数值规则不再使用 `--ink`
- [x] 1.2 将 `StatsCard.vue` 的 `.stats-card__stat strong` 改为 `color: var(--kpi-accent)`（或删除与共享件重复且会盖住 accent 的墨色声明）；验证：该文件主数值不再声明 `color: var(--ink)`，趋势 `small` 色不变。实现取后一路：删除墨色声明，避免模块越界借用 `--kpi-accent`（G6）

## 2. 回归

- [x] 2.1 检索全仓 `variant="entry"` 仍仅 `StatsCard`；验证：`frontend/` 内 `variant="entry"` 命中仅该包装
- [x] 2.2 在仪表盘打开统计入口行，抽查至少两张不同 accent 的卡：主数值与硬阴影同色，标题/描述/趋势不变；验证：浏览器可见行为符合 delta spec 两则场景。实测：在线设备/活跃智能体 valueColor 与 shadow RGB 一致、标题仍为 ink；报告页 `kpi` 变体 4 张数值仍为 ink
- [x] 2.3 `cd frontend && npm run lint:styles` 通过（颜色原子 / 无新增纯色字面量）
