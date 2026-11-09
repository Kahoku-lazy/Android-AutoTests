## Context

- AI 用量左列原本由五个 `StatsAppCard` 组成（`.ai-usage-kpis` 三列网格 + 第二行两个）。
- 数据字段：`stats.aiUsage.totalTokens.{today,total}`、`deepseekCost.{today,total}`、`cacheHitRate.total`。
- 平台卡片壳 `AppCard` 当前是「1px 细边 + 圆角 + 无阴影」，与 2026-11-09 的表纸风格一致。

## Goals / Non-Goals

**Goals：**

- 五个数字收敛成一张卡，层级固定为「命中率 → 当天 → 累计」。

**Non-Goals：**

- 不改数据口径、精度、接口；不改右侧智能体卡。

## Decisions

### 1. 用 AppCard + 1px 分隔线，而不是 KPI 卡拼贴

账单是一张“单据”，用卡片内的行分隔表达层级；继续用五张 KPI 卡会保留原来的问题（五个同权重数字）。行线取 `ink 8%`、栏线取 `ink 12%`，与表纸规则一致。

### 2. 缓存命中率作为唯一主指标

命中率是账单里唯一“比例型”指标，用 32px 大字 + 模块色（`--c-case`）放在第一栏；其余四项用 20px 数字两两成行。

### 3. 加载态用 SkeletonCard

账单卡结构固定，加载时整卡骨架，避免出现“0.00”假数据。

## 模块防火墙自检

- 只改 `modules/dashboard/index.vue` 与 `DashboardView.style.css`；`StatsAppCard` 仍在平台运营/测试资产使用，未改动。

## Risks / Trade-offs

- [左侧由五卡变一卡，左侧高度变短] → `.ch-ai__body` 两列 `align-items: stretch`，账单卡高度会撑满与右侧对齐；如显空可在卡内留白（当前已用行高自然填充）。
- [窄屏 640px 时两列明细仍并排] → 每列内容为短标签 + 数字，640px 下仍可读；后续可加 560px 断点转单列。
