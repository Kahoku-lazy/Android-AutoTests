## Why

「AI 用量」左侧现在是五张独立 KPI 卡（累计/当天用量、命中率、总/当天费用）：五个数字平铺，读不出「先看命中率、再看当天、最后看累计」的层级；同一条 DeepSeek 账单被拆成五块，视线要来回跳。需求方要求把它们聚合成一张「DeepSeek 账单」卡，按层级排列。

## What Changes

- 左侧五张 KPI 卡 → **一张聚合的「DeepSeek 账单」卡**：
  - 标题「DeepSeek 账单」；
  - 第一栏：缓存命中率（主指标，大字 + 1 位小数百分比）；
  - 第二行：当天用量（M，2 位小数）｜当天费用（3 位有效数字，元）；
  - 第三行：总用量（M，2 位小数）｜总费用（3 位有效数字，元）。
- 右侧智能体用量卡不变；数据口径、接口、精度规则全部不变。

## 关联文档

- 参考：用户提供的 Pipeline 卡片（标题 + 状态行 + 明细行）。
- 视觉用平台 `AppCard`（细墨线、圆角、无阴影）+ 1px ink 分隔线，与最新表纸风格一致。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `dashboard-ai-usage`：「五张 KPI 卡」要求改为「单张 DeepSeek 账单卡」的层级与字段要求。

## Impact

- 前端：`modules/dashboard/index.vue`（AI 用量左列结构）与 `DashboardView.style.css`（账单卡样式）。
- 后端 / 接口：无改动。
