## Why

仪表盘 / 报告 / BUG 概览的统计卡目前是「墨色虚线描边 + 模块色硬阴影」：描边和阴影是两种颜色、两种线型，卡片看起来像“草稿框贴了一块彩色板”。需求方要求把描边改成**与阴影同色的实线**，让卡片边界和投影读成一个整体。

## What Changes

- `KpiCard` 的默认描边：`2.5px dashed var(--ink)` → **`2.5px solid var(--kpi-accent)`**（与硬阴影同色）。
- 虚线白名单收敛：`KpiCard` 移出 `doodle-craft` 线型白名单，门禁 `check-dashed-whitelist.mjs` 的 OWNERS 只保留 `AgentRouteCard`。
- 视觉其余不变：圆角、硬阴影偏移、微倾、图钉/胶带装饰、`entry` 主数值色全部保持。

## 关联文档

- 同步更新 `.agents/skills/doodle-craft/SKILL.md` §线型规则 与 `references/components/cards.md` §3。

## Capabilities

### New Capabilities

- 无

### Modified Capabilities

- `frontend-doodle-kpi-card`: 卡壳由虚线描边改为「实线描边 = accent 阴影色」，并同步减少动效场景里的表述。

## Impact

- 前端：`shared/components/KpiCard.vue`、`tests/check-dashed-whitelist.mjs`；共享组件，仪表盘 / 报告页 / BUG 概览的统计卡同时生效。
- 后端 / 接口：无改动。
