## Context

动机见 `proposal.md` Why。共享 `KpiCard` 已把 `--kpi-accent` 设为 `color` prop（`StatsCard` 映射为模块色），`box-shadow` 用该变量；`entry` 主数值与 `StatsCard` 的 `strong` 现写死 `color: var(--ink)`。全仓仅 `StatsCard` 使用 `variant="entry"`；报告/知识库等走默认 `kpi` 变体。

## Goals / Non-Goals

**Goals:**

- `entry` 主数值色与硬阴影共用 `--kpi-accent`
- 去掉 `StatsCard` 对主数值墨色的覆盖
- 选择器限定在 `entry`，避免波及 `kpi` 变体

**Non-Goals:**

- 不改 `kpi` 变体数值色、不改 props / API、不改 count-up / 导航
- 不新增令牌、不改阴影几何
- 不把标题/趋势/图标改成 accent

## Decisions

1. **只改 `entry` 选择器，不改默认 `.kpi-card--kpi .kpi-card__value`**  
   理由：用户点选的是仪表盘入口卡居中数字；`kpi` 变体是紧凑指标行，墨色对比更稳。  
   备选：两变体一起改 — 否决，超出诉求且会改报告/知识库观感。

2. **颜色用已有 `--kpi-accent`，不新造 token**  
   理由：阴影已经用它；同卡同值。  
   备选：`color-mix` 加深 accent — 否决，用户要求与阴影色一致，不是另调一档。

3. **共享件与薄包装一起改**  
   `KpiCard` 的 `.kpi-card--entry .kpi-card__value` / `.kpi-card--entry .kpi-card__stat :deep(strong)` 改为 `var(--kpi-accent)`；`StatsCard` 的 `.stats-card__stat strong` 同步，否则 scoped 会盖住共享件。  
   备选：只改 `StatsCard` — 否决，入口卡契约应在共享件。

## 模块防火墙自检

- 跨 App import：不涉及后端
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 写库收敛到 api.py：无写库
- 前端不直连数据库；仪表盘不做写操作：仅 CSS，无新请求

## Risks / Trade-offs

- [浅色 accent 与白底对比下降] → 本变更按用户口径对齐阴影色，不另加深；若后续可读性不够再单独立单
- [选择器写宽波及 `kpi` 变体] → 规则挂在 `.kpi-card--entry` 下；改后检索 `.kpi-card--kpi .kpi-card__value` 仍为 `--ink`

## Migration Plan

无需数据迁移。回滚：还原上述两处 `color` 声明。
