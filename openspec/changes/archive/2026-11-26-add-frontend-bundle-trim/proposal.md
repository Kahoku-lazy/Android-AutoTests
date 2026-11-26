# Proposal: add-frontend-bundle-trim

## Why

`2026-11-26` 的体积基线里，**最大单块是 `useECharts`（gzip 368.7KB）**，比 `element-plus`（305.2KB）还大——
原因是 `useECharts.ts` 与 `TodayUsageChart.vue` 都写 `import * as echarts from "echarts"`，把整个 echarts 打进来。
平台只用到柱/线/饼三类图 + 5 个组件，全量导入多带了约 547KB（gzip 约 179KB）。

`add-bundle-size-budget` 的 design 里早把这条列为「体积来源」，但明说「不改任何页面代码」，所以一直悬着。

## What Changes

- 新增 `frontend/src/shared/helpers/echarts-setup.ts`：`echarts/core` + `BarChart` / `LineChart` / `PieChart`
  + `AxisPointer` / `Graphic` / `Grid` / `Legend` / `Tooltip` 组件 + `CanvasRenderer`，`echarts.use([...])` 后默认导出
- `shared/composables/useECharts.ts` 与 `modules/dashboard/components/TodayUsageChart.vue` 改引该 setup 模块
- **不动** `vite.config.js` 的 `manualChunks`、**不动** `bundle-budgets.json` 的任何阈值

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 纯打包策略调整，没有任何可观察行为变化，故 `skip_specs: true`）

## Impact

- 前端：3 个文件（1 新增 2 改 import）；页面行为、图表外观、交互完全不变
- 构建产物：最大单块 gzip 368.7 → 296.7KB；JS 总量 880.8 → 706.5KB（−19.8%）
- 预算：四项指标全部仍在预算内（12.9/15、55.6/62、296.7/406、706.5/961），本单不收紧也不放宽
- 回退：还原两处 import 并删 `echarts-setup.ts`，单 commit `git revert`
