## Context

- `KpiCard.vue` 是仪表盘入口卡、报告页 KPI、BUG 概览统计卡的唯一壳：`border: 2.5px dashed var(--ink)` + `box-shadow: 4px 4px 0 0 var(--kpi-accent)`。
- 线型白名单由 `.agents/skills/doodle-craft/SKILL.md` 定义、`frontend/tests/check-dashed-whitelist.mjs` 执行（OWNERS + 存量基线）。
- 需求方明确要求：描边改成与阴影同色的实线。

## Goals / Non-Goals

**Goals:**

- 描边与阴影同色，卡片边界读成一个整体；白名单与文档同步收紧到只剩 `AgentRouteCard`。

**Non-Goals:**

- 不改圆角、阴影偏移量、微倾、装饰（图钉/胶带）、`entry` 主数值色与交互。

## Decisions

### 1. 用 `var(--kpi-accent)` 而不是 `--ink`

描边必须与 `box-shadow` 同一个自定义属性，否则色值会漂移；`--kpi-accent` 已由 `props.color` 注入（`--kpi-accent: props.color`）。

### 2. 同步把 KpiCard 移出虚线白名单

规则是「虚线只属于白名单组件」；KpiCard 不再使用虚线后，若继续留在 OWNERS，未来回归不会被门禁拦住。因此同步移除 OWNERS 条目，并在 SKILL.md 记录变更与回退路径。

## 模块防火墙自检

- 只改 `shared/components/KpiCard.vue`、`tests/check-dashed-whitelist.mjs` 与两份技能文档；无模块业务代码改动。

## Risks / Trade-offs

- [描边与阴影同色后，卡片在小尺寸下对比度下降] → 实线 2.5px + 硬阴影 offset 仍能勾勒边界；如观感发虚可把描边加深一档（`color-mix(accent 70%, var(--ink))`），但本次不做。
- [共享组件影响三个页面] → 三处都是统计卡，视觉口径本来就应一致；不属于范围蔓延。
