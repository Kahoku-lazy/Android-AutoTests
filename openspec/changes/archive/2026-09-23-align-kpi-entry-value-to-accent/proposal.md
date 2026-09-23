## Why

仪表盘入口卡（`KpiCard` `entry` 变体）的硬偏移阴影已用模块 accent 色，居中主数值仍用 `--ink`，同一张卡上阴影与数字色不一致。现在做：把入口卡主数值改成与阴影同色，强化卡片身份色，不改交互与数据。

## What Changes

- `entry` 变体的主数值（`.kpi-card__value` / `strong`）颜色 MUST 使用卡片 accent（`--kpi-accent`），与 `box-shadow` 硬阴影同色
- 仪表盘薄包装 `StatsCard` 不得再把主数值锁成 `--ink`，以免盖住共享件规则
- 默认 `kpi` 变体（报告/知识库等紧凑指标行）主数值仍为 `--ink`，本变更不改其配色
- 标题、描述、趋势小字、图标描边、边框仍用现有 `--ink` / 次要色，不随 accent 改

非破坏性：无 API、无 props 变更。

## 关联文档

- `PRD-01-仪表盘`（KPI 概览入口卡视觉；无新业务需求，仅入口卡主数值配色与阴影对齐）

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `frontend-doodle-kpi-card`: 补充 `entry` 变体主数值色与硬阴影 accent 一致的可见要求；明确 `kpi` 变体主数值仍为墨色

## Impact

- 前端：`frontend/src/shared/components/KpiCard.vue`、`frontend/src/modules/dashboard/components/StatsCard.vue`
- 可见面：仪表盘统计入口行（`StatsCard` 唯一 `entry` 消费方）
- 不受影响：`kpi` 变体调用方（报告、知识库、任务详情等）
- 无后端 / 无 API / 无数据库
