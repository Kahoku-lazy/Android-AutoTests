## 1. 删除章节头 chip

- [x] 1.1 删除「平台运营」章节头的设备/智能体/任务/工作流 chip 行。验证：`frontend/src/modules/dashboard/index.vue` 的 `ch-ops` 章节内不再出现 `chip-row`，且 `设备 `、`智能体 `、`任务 `、`工作流 ` 四枚 chip 文案不存在。
- [x] 1.2 删除「AI 用量」章节头的角色·累计/角色·今日 chip 行。验证：`ch-ai` 章节内不再出现 `chip-row`，且 `角色·累计`、`角色·今日` 文案不存在。
- [x] 1.3 移除仅供角色 chip 使用的 `roleBreakdown`、`ROLE_LABELS` 与页面解构。验证：`rg "roleBreakdown|ROLE_LABELS"` 无匹配，`npm run typecheck` 通过。
- [x] 1.4 移除失去唯一消费者的 `.chip--yellow`、`.chip--rose`、`.chip--violet` 样式，保留 `.chip--teal` 与「测试资产」用例 chip。验证：`frontend/src/modules/dashboard/index.vue` 仍有 `用例` chip，`rg "chip--(yellow|rose|violet)"` 无匹配。

## 2. 验证与关单

- [x] 2.1 仪表盘相关单测通过：`npx vitest run tests/dashboard/p0/StatsCard.spec.ts tests/dashboard/p1/DashboardView.logic.spec.ts`。
- [x] 2.2 前端类型检查与构建通过：`npm run build:check`。
- [x] 2.3 运行前端门禁 `vue-frontend-check`，确认无硬编码字号/颜色与布局裁剪问题。
- [x] 2.4 归档前把主 spec `dashboard-chapter-boards` 的 Purpose 中 chip 摘要描述同步为「方标 + eyebrow + 标题」层级，并确认 `openspec validate "2026-10-21-dashboard-remove-chapter-chips" --strict` 通过。
