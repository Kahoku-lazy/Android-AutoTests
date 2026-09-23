## Why

仪表盘「AI 用量」章节头的累计 Token、任务、费用 chip 与下方 KPI 卡数值重复；该区每张卡还带「进入」按钮，但全部指向同一 `/ai-assistant`。章节头拥挤、卡片底栏重复，扫描成本高。

## What Changes

- 去掉 AI 用量章节头的三枚汇总 chip：累计 Token、任务、费用
- 保留分角色 chip（角色·累计 / 角色·今日）
- AI 用量区内 KPI 卡不再渲染「进入」按钮；整卡仍可点进 `/ai-assistant`（有 `path` 时）
- 其它章节（平台运营、测试资产）的 chip 与「进入」不变
- 不改 API、不改 Token/费用计算、不改共享 `KpiCard` 默认行为

## 关联文档

- 主规格：`openspec/specs/dashboard-chapter-boards/spec.md`
- 用量区块：`openspec/specs/dashboard-ai-usage/spec.md`

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `dashboard-chapter-boards`：AI 用量章节头只保留角色拆解 chip，不再重复 Token/任务/费用
- `dashboard-ai-usage`：AI 用量 KPI 卡展示今日+累计，不再带独立「进入」按钮

## Impact

- `frontend/src/modules/dashboard/index.vue`（章节头 chip）
- `frontend/src/modules/dashboard/components/StatsCard.vue`（可选隐藏「进入」）
- 相关前端单测（StatsCard 进入按钮、若有 dashboard 布局断言）
- 不改：`apps/`、仪表盘 API、`KpiCard` 默认 `enterLabel`
