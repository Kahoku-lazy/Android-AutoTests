## Why

仪表盘「AI 用量」第 4 张 KPI 卡展示的是「平均每任务 Token」，用户真正关心的是当天消耗了多少 token，平均值既不直观，也无法直接与「累计 Token」对照；且千（K）单位在 token 量级上需要额外换算。

## What Changes

- 「AI 用量」第 4 张 KPI 卡标题由「平均每任务 Token」改为「当天 Token 用量」。
- 主数值改为当天（today）token 合计量，按百万（M）显示并保留 2 位小数，不再除以任务数，不再使用千（K）单位。
- 该卡不显示副标题（不再出现「今日 …」文案）；其余四张 KPI 卡的数值与副标题口径不变。
- 统计接口与 `avg_tokens_per_task` 字段保持不变（非破坏性），仅前端不再使用该字段。

## 关联文档

- PRD-01 仪表盘

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-ai-usage`: 「仪表盘展示 AI 用量区块」的卡片集合与第 4 张卡数值口径变化

## Impact

- `frontend/src/modules/dashboard/index.vue`：第 4 张 KPI 卡的标题、数值与副标题
- `frontend/src/modules/dashboard/components/StatsCard.vue`：支持不渲染副标题
- `frontend/src/modules/dashboard/DashboardView.logic.ts`：移除仅供旧卡使用的千（K）换算助手
- `frontend/tests/dashboard/`：补充/调整对应单测
- 后端聚合与 `GET /api/dashboard/stats/` 契约不变
