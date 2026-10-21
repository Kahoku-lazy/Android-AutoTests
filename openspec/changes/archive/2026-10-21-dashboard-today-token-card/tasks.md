## 1. 卡片展示

- [x] 1.1 「AI 用量」第 4 张 KPI 卡标题改为「当天 Token 用量」，主数值取当天 token 合计并按百万（M）、2 位小数显示，不再取平均、不再使用 K 单位，且不显示副标题。验证：`frontend/src/modules/dashboard/index.vue` 中该卡使用 `toMillions(stats.aiUsage.totalTokens.today)`、`suffix="M"`、`hide-desc`，且不再引用 `avgTokensPerTask`。
- [x] 1.2 `StatsCard` 增加显式「不显示副标题」开关，未传该开关的卡片仍回退「核心指标实时更新」。验证：新增单测覆盖 `hideDesc=true` 时 `.kpi-card__desc` 不存在，既有 `desc 缺省时显示默认描述` 用例继续通过。
- [x] 1.3 删除仅旧卡使用的 `toK()` 并同步注释，确认无残留调用。验证：`rg "toK\("` 无匹配，`npm run typecheck` 通过。

## 2. 验证与关单

- [x] 2.1 运行仪表盘相关单测并通过：`npx vitest run tests/dashboard/p0/StatsCard.spec.ts tests/dashboard/p1/DashboardView.logic.spec.ts`。
- [x] 2.2 前端构建与类型检查通过：`npm run build:check`。
- [x] 2.3 运行前端门禁 `vue-frontend-check`，确认无硬编码字号/颜色与布局裁剪问题。
- [x] 2.4 归档前把主 spec 的 Purpose 中「平均每任务 Token」同步为「当天 Token 用量」，并确认 `openspec validate "2026-10-21-dashboard-today-token-card" --strict` 通过。
