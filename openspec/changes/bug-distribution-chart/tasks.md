## 1. 数据与配置

- [x] 1.1 新建 `helpers/bugDistribution.ts`：`BUG_STATUS_SLICES` / `BUG_CATEGORY_BARS` 常量、`statusSeriesData()` / `categorySeriesData()` / `buildDistributionOption(summary)` 纯函数。验证：`vue-tsc` 通过。**验证结果**：tsc 0。
- [x] 1.2 option 只读 `summary`，不遍历 `items`；图例只列三个状态，条形图 y 轴用类型名。验证：单测断言 series 数据与 `summary` 一致。**验证结果**：见 3.1。

## 2. 组件与页面

- [x] 2.1 新建 `components/BugDistributionChart.vue`：`useECharts` 挂载，容器高 260px，带 `role="img"` 与 aria-label。验证：build 通过。**验证结果**：build 41.8s 通过。
- [x] 2.2 `index.vue` 在「BUG 概览」与「BUG 单」之间插入「BUG 分布」区块（`doc-section` + `doc-section__header` + 图表）。验证：页面结构与其它区块同一皮肤。**验证结果**：已插入，复用 `doc-section` 样式。

## 3. 测试与门禁

- [x] 3.1 `tests/bug-manager/p0/bugDistribution.spec.ts`：状态/类型映射顺序、全零、圆心总数、series 与图例同源，共 5 条。验证：`npx vitest run tests/bug-manager` 通过。**验证结果**：2 文件 10 passed。
- [x] 3.2 门禁：`npx vue-tsc --noEmit`、`npm run build:check`、`npm run lint:styles`、`npm run lint:lines`。验证：全绿。**验证结果**：tsc 0；build 41.8s；批 2 通过（批 3 仍 50 处既有）；虚线 0 处。
- [ ] 3.3 目视：环形图与条形图随筛选变化、窄屏不重叠。验证：用户确认。
