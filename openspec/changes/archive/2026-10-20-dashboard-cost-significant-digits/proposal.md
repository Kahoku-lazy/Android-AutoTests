## Why

仪表盘 DeepSeek 费用卡片把小时用量的 8 位小数原样铺开，`1.43860156` 在卡片里挤成一长串。汇总卡只需要看数量级。

## What Changes

- DeepSeek 费用卡片的累计值与「今日」改为三位有效数字，不使用科学计数法。`1.43860156` 显示为 `1.44`。
- 统计接口仍返回小数点后 8 位。智能体明细卡的总费用仍是 8 位小数字符串。

## 关联文档

- PRD-01 仪表盘

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-ai-usage`: DeepSeek 费用卡片按三位有效数字显示

## Impact

- `frontend/src/modules/dashboard/index.vue`：费用卡与「今日」文案
- `frontend/src/modules/dashboard/components/StatsCard.vue`、`frontend/src/shared/animations.ts`：有效数字格式
- 后端聚合与智能体卡不改
