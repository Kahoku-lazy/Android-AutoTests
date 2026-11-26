# Tasks: add-frontend-bundle-trim

> 格式：**动作 → 完成判据**。

## 1. 按需注册

- [x] 1.1 新增 `frontend/src/shared/helpers/echarts-setup.ts`：`echarts/core` + `Bar/Line/Pie` + `AxisPointer/Graphic/Grid/Legend/Tooltip` + `CanvasRenderer`，`echarts.use([...])` 后默认导出。
  判据：`grep -rn 'from "echarts"' frontend/src` 命中 0。
- [x] 1.2 `shared/composables/useECharts.ts` 与 `modules/dashboard/components/TodayUsageChart.vue` 改引 `@/shared/helpers/echarts-setup`。
  判据：`vue-tsc` 通过；两个文件的 diff 只有 import 一行。

## 2. 体积实测

- [x] 2.1 同一台机、同一命令（`npx vite build` + `python utils/check_bundle_budget.py`）测基线与本单两次。
  判据：基线 `368.7 / 880.8`（largest / total），本单 `296.7 / 706.5`；数字记入 design.md 的对照表。
- [x] 2.2 四项预算全部仍在预算内，**不放宽也不收紧** `bundle-budgets.json`。
  判据：`check_bundle_budget` 输出 `12.9/15`、`55.6/62`、`296.7/406`、`706.5/961` 四项 ok，且该文件 diff 为空。

## 3. 分支实验（不落地，只留记录）

- [x] 3.1 测「再去掉 `manualChunks` 里的 element-plus」的效果，结论写进 design D3。
  判据：`entry_js 44.5 / largest 194.4 / total 579.0` 三个数字与「入口预算会被突破」的判断都在 design 里。
- [x] 3.2 明确不把该实验带进本单（`vite.config.js` 在本单 diff 中为空）。
  判据：`git diff origin/Kahoku -- frontend/vite.config.js` 无输出。

## 4. 门禁

- [x] 4.1 前端十条门禁全过。
  判据：`utils/check_gates.py --only "vitest,vite-build,bundle-budget,prettier,eslint,dashed-whitelist,vue-tsc,prettier-ts,style-gates,cred-frontend"` 十项 PASS。
- [x] 4.2 `openspec validate add-frontend-bundle-trim --strict` 通过。
  判据：输出 `is valid`。
