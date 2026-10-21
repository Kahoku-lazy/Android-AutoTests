## Why

仪表盘「AI 用量」区块左侧第一行的「累计用量」「当天用量」「缓存命中率」三张卡现在没有副标题，而第二行的「总费用」「当天费用」副标题是「DeepSeek」；同一区块里同源数据一半标注、一半空白，用户看不出这些数字来自哪家模型的开销口径。给第一行补齐同一个副标题，使五张 KPI 卡的数据来源标注一致。

## What Changes

- 「累计用量」「当天用量」「缓存命中率」三张卡改为显示副标题「DeepSeek」，与「总费用」「当天费用」保持一致。
- 这五张卡的副标题口径统一为：来自 DeepSeek 的用量与费用；不再保留「无副标题」写法。
- 移除 `StatsCard` 上仅为这三张卡引入的 `hideDesc` 开关（改动后全仓无调用方），副标题文案统一回到 `desc` 单一入口；`desc` 缺省时仍回退「核心指标实时更新」的既有行为不变。
- 同步删除/改写覆盖 `hideDesc` 的单测，并修正 `dashboard-ai-usage` 中「这三张卡 MUST NOT 显示副标题」的验收条款。
- 非 BREAKING：数值、口径、跳转、布局、接口字段均不变，只增加三处副标题。

## 关联文档

- PRD-01 仪表盘（AI 用量区块的 KPI 卡展示口径）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `dashboard-ai-usage`: 「仪表盘展示 AI 用量区块」要求从「第一行三张卡不显示副标题」改为「五张 KPI 卡的副标题均为 DeepSeek」；对应场景中「三张无副标题卡片」与「不显示副标题」的断言同步修改。

## Impact

- 前端页面：`frontend/src/modules/dashboard/index.vue`（三张 KPI 卡的 `desc` / `hide-desc`）
- 前端共享件：`frontend/src/modules/dashboard/components/StatsCard.vue`（删除 `hideDesc` 属性与其 computed 分支）
- 前端单测：`frontend/tests/dashboard/p0/StatsCard.spec.ts`（`hideDesc` 用例改为覆盖 `desc` 渲染）
- 验收标准：`openspec/specs/dashboard-ai-usage/spec.md`（区块展示要求与两个场景）
- 后端接口、数据模型、路由、依赖均不变
