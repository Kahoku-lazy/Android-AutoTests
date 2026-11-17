# 任务：仪表盘数值深彩渐变

- [x] 1.1 `shared/components/KpiCard.vue`：`kpi` 变体数值渐变改为 accent 混墨 48%→30%，回退色取终点
- [x] 1.2 `shared/components/KpiCard.vue`：`entry` 变体数值渐变同步，回退色取终点
- [x] 1.3 `dashboard/DashboardView.style.css`：账单卡 `hero-value` 与 `cell b` 改同一配方（替换原三段式）
- [x] 1.4 `.agents/skills/doodle-craft/references/components/cards.md` §3：更新数值口径，写明旧口径作废
- [x] 1.5 实跑 computed：`linear-gradient(90deg, srgb 0.263/0.443/0.297, srgb 0.208/0.321/0.239)`（绿卡）与青卡 `0.208/0.447/0.442 → 0.174/0.324/0.329`
- [x] 1.6 对比度实测（python，WCAG）：1.14~3.02:1 → **7.2~10.6:1**
- [x] 1.7 `npm run typecheck`、`npm run lint:styles` 无新增违规；截图 `temps/dashboard-after-colors.png`
