## 1. 仪表盘 KPI 卡副标题

- [x] 1.1 `frontend/src/modules/dashboard/index.vue`：删掉「累计用量」「当天用量」「缓存命中率」三张 `StatsCard` 上的 `hide-desc`，各补 `desc="DeepSeek"`。验证：`rg "hide-desc" frontend/src` 无匹配，且该文件内 5 张 AI KPI 卡均带 `desc="DeepSeek"`。
- [x] 1.2 确认副标题渲染与第二行模板一致（`.kpi-card__desc` 文案为「DeepSeek」，不出现「核心指标实时更新」）。验证：真实页面截图（Playwright，1686×1000 视口）读到五张卡 subtitle 均为 `DeepSeek`，与第二行同款同色同字号。

## 2. 清理死开关

- [x] 2.1 `frontend/src/modules/dashboard/components/StatsCard.vue`：删除 `hideDesc` 属性声明、默认值与 `descText` 中的 `hideDesc` 分支，保留 `desc || "核心指标实时更新"` 回退。验证：`rg "hideDesc" frontend/src` 无匹配，`npx vue-tsc --noEmit` 通过。

## 3. 单测与验收标准

- [x] 3.1 `frontend/tests/dashboard/p0/StatsCard.spec.ts`：把 `hideDesc=true` 用例替换为「显式传 `desc` 时渲染该文案且不出现缺省文案」。验证：`npm run test -- tests/dashboard/p0/StatsCard.spec.ts` 通过（13/13，缺省文案用例保持通过）。
- [x] 3.2 主 spec 由归档时的 delta 合并更新，本阶段不改 `openspec/specs/dashboard-ai-usage/spec.md`。验证：`openspec validate "2026-10-21-dashboard-ai-usage-deepseek-desc" --strict` 通过；归档后复核主 spec 内不再出现「MUST NOT 显示副标题」。

## 4. 门禁与验收

- [x] 4.1 前端门禁：`cd frontend && npx vue-tsc --noEmit && npm run lint:styles && npm run build` 全绿。
- [x] 4.2 人工验收：打开仪表盘「AI 用量」区块，确认第一行三张卡副标题为「DeepSeek」、与第二行保持一致，两行卡片仍等高对齐、无裁剪、无布局跳变。
