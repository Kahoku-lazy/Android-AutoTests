## Context

- 现状：`frontend/src/shared/components/KpiCard.vue` 服务报告 / AI 等紧凑指标；`frontend/src/modules/dashboard/components/StatsCard.vue` 服务仪表盘入口卡。两者均为清新风（实线、大圆角、模糊阴影）。
- 目标视觉 DNA：`temps/hand-drawn-doodle-sidebar.html` 色板卡 #5（Yellow Marker）+ 方案原型 `temps/prototype-doodle-kpi-stats-card.html`。
- 技能规格：`.agents/skills/doodle-craft/references/components.md` §13；落地取舍以模版侧栏为准——**边框用 dashed**，accent 用 8 模块色，阴影色随 accent 轮换。
- 动机与范围见 `proposal.md`。

## Goals / Non-Goals

**Goals:**

- 单一共享壳承载 `kpi` / `entry` 双变体
- 现有 `KpiCard` 调用方零改或仅改 class 即可换皮
- 仪表盘 StatsCard 收敛为共享 `entry`（薄包装可保留 count-up / 路由逻辑）
- 同步技能文档与前端 AGENTS 共享件说明

**Non-Goals:**

- 不改 `AppCard` / 内容块卡片体系
- 不改后端仪表盘 API 或字段计算
- 不引入新的图表库 / 动效库
- 不做全站所有卡片（列表卡、设备卡等）一次性换皮

## Decisions

### 1. 升级 `KpiCard`，不新建第三组件

- **选择**：在 `KpiCard.vue` 增加 `variant: 'kpi' | 'entry'`（默认 `kpi`）。
- **理由**：符合 AGENTS「同场景必用共享件」；避免 `DoodleStatCard` + 旧卡长期双 API。
- **备选**：新建 `DoodleStatCard` 并存（方案 C）——仅当一次改消费方风险过高时采用；本变更已确认方案 B，不采用。

### 2. 仪表盘 `StatsCard` 保留为薄包装

- **选择**：`StatsCard.vue` 继续持有 count-up、loading 骨架、`path` 路由、`live` / `trend` 等仪表盘特有逻辑，模板改为渲染 `<KpiCard variant="entry" ...>` 或等价插槽映射。
- **理由**：把视觉壳与业务行为拆开；单测可继续针对仪表盘行为，视觉断言指向共享类名。
- **备选**：删除 `StatsCard`、页面直连 `KpiCard`——会把 count-up 等逻辑推入页面或共享层，范围更大。

### 3. 视觉令牌与装饰

- **选择**：壳样式优先用现有 `--ink` / `--c-*` / 间距圆角令牌；硬阴影用 `box-shadow: Npx Npx 0 0 <accent>`；微倾用 CSS 变量 `--tilt`，网格 `nth-child` 或父级传入；装饰 `deco: 'none' | 'pin' | 'tape'`（默认 `none` 或 entry 默认轻度装饰，以实现时可读性为准）。
- **理由**：对齐色板卡 DNA，避免再引入一套色值。
- **备选**：完全照抄 doodle-craft §13 的 solid 3px + Caveat——与侧栏模版 dashed 不一致；本变更明确以侧栏模版 dashed 为准，并回写技能文档。

### 4. 兼容策略

- **选择**：保留 `label` / `value` / `color` / `shape` / default slot / `click`；`entry` 新增 `icon`（slot）、`desc`、`path` 或 `enterLabel`、`live` 等。
- **理由**：报告与 AI 页面无需改调用即可换皮。

## 模块防火墙自检

- 跨 App import：不涉及；纯前端 `frontend/` 共享组件与 dashboard 模块。
- 禁止跨 App import service/runner/consumer/state_machine：不涉及。
- 写操作收敛 api.py：不涉及；仪表盘保持只读展示。
- 前端不直连数据库：不涉及。
- 新跨模块依赖：无后端依赖；前端仅 dashboard → shared 单向依赖（已存在模式）。

## Risks / Trade-offs

- [换皮影响面] 所有 `KpiCard` 消费方同时变样 → 用默认 `kpi` 变体保证信息结构不变；发版前用原型页与关键页目视对比。
- [StatsCard 逻辑与壳耦合] count-up 与骨架若硬塞进共享卡 → 保持 StatsCard 薄包装，共享卡只接收已格式化 `value` 文本或简单 number。
- [技能文档与实现不一致] dashed vs solid → 实现后立刻改 `components.md` §13，避免下次复制错误规格。
- [动效与 a11y] 微倾在 reduced-motion 下需关闭 → 规格已约束；实现时用 media query。

## Migration Plan

1. 先改 `KpiCard` 壳 + `kpi` 变体，确认报告 / AI 页视觉。
2. 扩展 `entry` 变体，改 `StatsCard` 薄包装与仪表盘页。
3. 更新单测、AGENTS、doodle-craft 规格。
4. 回滚：还原 `KpiCard.vue` / `StatsCard.vue` 即可；无数据迁移。

## Open Questions

（无；方案 B 与原型已确认。装饰默认开/关在实现时按可读性二选一，不改变规格场景。）
