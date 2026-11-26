# Design: add-frontend-bundle-trim

## Context

同一份构建（Windows 11 / node 24.11.1 / `npx vite build` / `check_bundle_budget` 复算 gzip level 9）三次实测：

| 场景 | entry_js | entry_css | largest_chunk | total_js | 最大块是谁 |
|---|---:|---:|---:|---:|---|
| 基线（`origin/Kahoku` 5ddebe95） | 12.9 | 55.6 | 368.7 | 880.8 | `useECharts` 1128.6KB / gzip 379.4 |
| **本单（echarts 按需）** | **12.9** | **55.6** | **296.7** | **706.5** | `element-plus` 947.3KB / gzip 305.2 |
| 附加实验（再拆 element-plus 手工 chunk） | 44.5 | 55.6 | 194.4 | 579.0 | `useECharts` gzip 194.4 |

## Goals / Non-Goals

**Goals**

- 把 echarts 全量导入换成按需注册，且四项预算指标都仍在预算内（不放宽、不收紧）
- 零行为变化：图表样式、交互、数据口径一字不动

**Non-Goals**

- 不碰 `vite.config.js` 的 `manualChunks`（实验见 D3，需另做决策）
- 不动 `bundle-budgets.json`（收紧留到单独 PR，避免和别的在制 PR 撞车）
- 不动 `element-plus/dist/index.css` 的引入方式（属另一类问题：CSS 体积）

## Decisions

### D1 只注册用到的 3 类图 + 5 个组件

`BarChart` / `LineChart` / `PieChart` + `AxisPointer` / `Graphic` / `Grid` / `Legend` / `Tooltip` + `CanvasRenderer`。
依据：全仓 `useECharts` 的调用方只有 5 处（`TaskCountBars`、`BugDistributionChart`、`ModelLineChart`、`TrendBarChart`、`TodayUsageChart`），
覆盖柱、线、饼三类；`SVGRenderer` 无人使用。

### D2 setup 模块单独成文件，而不是散落在 `useECharts` 里

`TodayUsageChart` 直接用了 `echarts.graphic.LinearGradient`（自绘渐变），所以它也需要那个已注册的实例；
统一从 `shared/helpers/echarts-setup` 取，避免「谁先 import 谁注册」的隐式依赖。

### D3 `manualChunks` 的 element-plus 手工分块：实测有效但不进本单

把 `manualChunks` 里的 `element-plus` 去掉后（实验第三行）：

- 收益：`total_js` 706.5 → 579.0（再降 18%），`largest_chunk` 296.7 → 194.4
- 代价：`entry_js` 12.9 → **44.5**，超出现预算 15KB 近 3 倍——因为 element-plus 被折进首屏必载的入口块

这不是「build 变红所以要调阈值」能糊过去的事：**入口 JS 预算是首屏护栏**，抬它属于策略变更。
因此本单不碰，留作独立决策（要落地需同时把 `entry_js_kb` 预算按实测重标定并写明理由）。

## Risks / Trade-offs

- [按需注册漏了某个组件导致运行时报错] → 5 个调用方的 option 都只用 bar/line/pie + grid/legend/tooltip/axisPointer/graphic；
  且 `vue-tsc` + `vitest`（图表组件有渲染用例）+ `vite build` 三道门禁同时覆盖
- [将来有人又写 `import * as echarts from "echarts"`] → 本单的收益会悄悄回退；尚无静态守卫，建议后续加一条 `tests/arch` 断言（不在本单）
- [预算不变但仍有余量，可能出现回退] → 余量是故意的：收紧需要单独 PR 并把 baseline+budget 一起重标定

## Migration Plan

1. 落 `echarts-setup.ts` 与两处 import
2. `npx vite build` + `check_bundle_budget` 取新数字，与基线逐项比对
3. 前端十条门禁

**Rollback**：还原两个 import、删 `echarts-setup.ts`，单 commit `git revert`。
