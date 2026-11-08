## Context

- BUG 页当前结构：`WorkbenchHeader` → `.doc-body` → 「BUG 概览」（4 张 KpiCard）→ 「BUG 单」表格（筛选 + 分页）。
- 列表接口返回 `summary`（`total / ui_automation / case_authoring / open / resolved / ignored`），无时间序列字段。
- 报告页图表统一走 `shared/composables/useECharts` + 模块内常量色的模式。

## Goals / Non-Goals

**Goals:**

- 用现有 `summary` 表达「状态分布 + 类型构成」，不新增接口、不改后端。

**Non-Goals:**

- 不做按天趋势（缺少时间序列接口，硬用当前页 `items` 聚合会因分页失真）；后续如需要，应新增 `/api/bugs/stats/`。

## Decisions

### 1. 双图合一卡：环形图 + 条形图

一张 ECharts 实例内放 pie（左）与 bar（右）：状态维度适合环形（占比），类型维度只有两项，横向条形更省空间。单卡避免页面上再出现一块「半空」的区域。

### 2. 数据只来自 `summary`

`summary` 由后端聚合，口径与 KPI 卡一致；若前端遍历 `items` 聚合，分页/截断会导致数字与 KPI 对不上——这是明确排除的做法。

### 3. 配置抽成纯函数 `buildDistributionOption`

ECharts option 由 `helpers/bugDistribution.ts` 生成，组件只负责挂载与尺寸；单测直接断言 series 数据，不需要渲染环境。

## 模块防火墙自检

- 只改 `frontend/src/modules/bug-manager/**` 与 `frontend/tests/bug-manager/**`；图表底座复用 `shared/composables/useECharts`，未改共享层。

## Risks / Trade-offs

- [颜色硬编码在 TS 常量里] → 与报告页 `CHART_COLORS` 同一模式；后续若要统一，可把图表色板提升到 `shared/constants/chart.ts`。
- [环形图在窄屏被条形图挤压] → 图表容器 `height: 260px`，`grid.left` 用 54% 固定分栏；若后续加响应式，可在 720px 以下改为上下堆叠。
