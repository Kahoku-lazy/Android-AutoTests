## Why

仪表盘 `StatsCard` 与共享 `KpiCard` 仍是实线细边 / 大圆角 / 模糊阴影，与 hand-drawn-doodle 色板卡（虚线边 + 微倾 + 色块硬阴影）两套语言；后续指标卡若只改仪表盘会双实现。需要把「手绘卡壳」收敛到共享组件，供仪表盘入口卡与各模块 KPI 共用。

## What Changes

- 升级 `shared/components/KpiCard.vue` 为 doodle 壳：虚线边、近直角、硬偏移色阴影、可选微倾 / 图钉 / 胶带，accent 走模块色 `--c-*`
- 新增 `variant`：`kpi`（默认，兼容现有调用）与 `entry`（图标 + 标题 + 数值 + 描述 +「进入」，承接仪表盘 StatsCard）
- 仪表盘 `StatsCard` 改为薄包装或直接改用共享 `KpiCard variant="entry"`，去掉私有清新风样式
- 同步 `.agents/skills/doodle-craft/references/components.md` §13 KPI 规格与 `frontend/AGENTS.md` 共享件说明
- 更新 / 补齐相关单测（`StatsCard` / `KpiCard`）
- **BREAKING**：无 API/路由破坏；视觉为有意换皮。现有 `KpiCard` 的 `label` / `value` / `color` / `shape` / `@click` 保持兼容；`entry` 为新增 props

## 关联文档

- 视觉模版：`temps/hand-drawn-doodle-sidebar.html`（`#page-palette` Yellow Marker 色板卡 DNA）
- 方案原型：`temps/prototype-doodle-kpi-stats-card.html`（方案 B 可点对比）
- 组件规格：`.agents/skills/doodle-craft/references/components.md` §13 `.kpi-card`
- 前端共享件口径：`frontend/AGENTS.md`（`KpiCard` 条目）
- 说明：`dev_docs/文档编号对照表.md` 不存在；无对应 PRD/ARCH 编号文档。本变更属前端共享视觉组件统一，不改业务接口

## Capabilities

### New Capabilities

- `frontend-doodle-kpi-card`：共享 KPI/入口统计卡的 doodle 视觉与双变体契约（`kpi` / `entry`）、装饰与 a11y（可点击、键盘、reduced-motion）

### Modified Capabilities

（无；`openspec/specs/` 下暂无既有 KPI 卡能力）

## Impact

- 前端共享：`frontend/src/shared/components/KpiCard.vue`（及必要的 tokens / 样式令牌若缺阴影色）
- 仪表盘：`frontend/src/modules/dashboard/components/StatsCard.vue`、`frontend/src/modules/dashboard/index.vue`（及现有 `StatsCard` 单测）
- 既有 `KpiCard` 消费方（自动换皮）：`report-generator`（index / ReportDetail / TaskReport / CaseBreakdown）、`ai-assistant`（KnowledgeBase / TaskDetailPage）
- 技能与文档：`doodle-craft/references/components.md`、`frontend/AGENTS.md`
- 测试：`frontend/tests/` 相关单测、`cd frontend && npm run typecheck`
- 不影响：后端 API、鉴权、路由表、`AppCard` 内容块大改（明确非目标）
