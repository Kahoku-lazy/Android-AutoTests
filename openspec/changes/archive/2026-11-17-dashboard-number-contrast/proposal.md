# 仪表盘数值配色：深彩渐变（可读性修订）

## Why

仪表盘两类卡片的**主数值**几乎读不动：共享 `KpiCard` 的数值渐变是「accent 80% 混纸色 → 30% 混纸色」，实测对比度只有 **1.1~3.0:1**（28px 粗体的大字号门槛是 3:1，多数卡连门槛都不到）；AI 用量「平台账单」卡里的 `71.7%`、`0.60M` 用的是同一思路的三段渐变，末段混到 20% 纸色，更淡。这正是当前 spec 里「KPI 主数值取 accent 的 80%→30% 渐变」那条要求的直接结果。

需求方要求：**结合纸面背景做一套可读性强、不刺眼、仍保留渐变多彩**的数值配色。

## What Changes

- 共享 `KpiCard`（`kpi` 与 `entry` 两个变体）主数值渐变改为**深彩渐变**：`accent 与墨色 48% → 30%` 的同色相两端；不支持 `background-clip: text` 时回落到终点色。
- AI 用量「平台账单」卡的 `缓存命中率` 与四个明细数值改成同一套渐变（原三段式含 20% 纸色端，作废）。
- 卡片其余部分**不变**：描边、三层硬影、图标底色、标题与描述仍取模块色与墨色。
- 作废旧口径：**不再混纸色**、不再以「80%→30%」为数值区间。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-doodle-kpi-card`：删除「KPI 主数值取 accent 的 80%→30% 渐变」，新增「KPI 主数值取深彩渐变（accent 与墨色 48%→30%）」。
- `dashboard-ai-usage`：新增「AI 用量区块的数值配色」要求。

## Impact

- 前端共享件：`shared/components/KpiCard.vue`（两处数值渐变 + 回退色）。**影响四处消费方**：仪表盘、BUG 单、测试报告、任务清单的统计卡——它们原本也读不动，按需求方确认一并修正。
- 前端 `dashboard`：`DashboardView.style.css`（账单卡两处数值渐变）。
- 样式登记：`.agents/skills/doodle-craft/references/components/cards.md` §3 更新 KpiCard 数值口径并写明旧口径作废。
- 不动接口、不动数据、不动布局。
