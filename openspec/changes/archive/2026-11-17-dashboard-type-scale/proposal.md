# 仪表盘字号口径与 KPI 数值渐变区间

## Why

仪表盘里 12px 的次要文字太多（描述、字段名、时间、标签），与实际阅读距离不匹配；卡片标题和正文只差一档，层级不明显。KPI 数值的渐变从「深墨」拉到「接近纸色」，跨度太大，同一个数字左半和右半像两种颜色。

## What Changes

- 数值渐变收到 accent 的 **80% → 30%** 区间内（两端都是 accent 与纸色的混合），不再混墨色进场、也不再用满色 100% 与 20% 的淡化端。
- 卡片标题统一 **16px**（原 14px）：在线设备 / 活跃智能体 / 运行中任务 / 任务数量、DEEPSEEK 账单、用量趋势、测试用例区块标题。
- 其余文本统一 **14px**（原 12px）：描述、字段名、时间、标签、小字。
- 大标题（平台概览 / AI 用量）与数值字号 **不变**（20px / 28px）。
- 图表内部文字（ECharts 的轴标签与图例，代码里是 `fontSize: 12`）**不动**：那是 canvas 内绘制，不在 CSS 字号口径内。

## 关联文档

无关联 PRD 编号：需求方 2026-11-17 按仪表盘截图直接提出的字号与渐变口径。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-doodle-kpi-card`：主数值配色规则改写为「accent 的 80%→30% 渐变」，并补一条仪表盘信息层级字号要求。

## Impact

- `frontend/src/shared/components/KpiCard.vue`（两处数值渐变、标题 16、描述/小字 14）
- `frontend/src/modules/dashboard/DashboardView.style.css`（6 处 12→14、2 处标题 14→16）
- `frontend/src/modules/dashboard/components/StatsCard.vue`、`ActivityTimeline.vue`、`TaskResultPanel.vue`（共 8 处 12→14）
