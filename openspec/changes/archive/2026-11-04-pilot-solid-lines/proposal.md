## Why

线型规则已定为「虚线只属于 KpiCard / AgentRouteCard 两个组件皮肤」（`.agents/skills/doodle-craft/SKILL.md`），但代码里还有 22 个文件、37 处虚线。全量翻掉会一次改动所有页面的观感，风险不可控；先拿视觉最重的两个页面（任务详情、仪表盘）试点，确认实线观感后再推广。

## What Changes

- **任务详情**：`CaseImportCard`、`TaskMediaThumb`（外框与占位）、`StepLogCheck`、`StepLogEvidence`、`TaskAttemptCard` 的虚线框改 `1px solid`。
- **仪表盘**：页内的 `.ac-card` 卡片（7 个图表/趋势卡）改为实线白卡——只在本页作用域覆盖，不动全局 `workbench-theme.css`；`ActivityTimeline` 分隔线、`.dashboard__footer`、`.usage-empty` 同步改实线。
- **不动**：KpiCard（白名单）、AgentRouteCard、其它页面与全局 AppCard / 对话框 / 抽屉。
- **门禁**：把试点页涉及的 7 个文件从 `check-dashed-whitelist.mjs` 基线里删除，改为 0 容忍。

## 关联文档

- 纯视觉试点，无 PRD 编号；规则来源 `.agents/skills/doodle-craft/SKILL.md` §线型规则。
- 上一增量：`openspec/changes/archive/2026-11-03-*` 与 `openspec/changes/task-detail-card-style`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 纯视觉线型调整，`.openspec.yaml` 已置 `skip_specs: true`）

## Impact

- 前端：`modules/task-list/components/{CaseImportCard,TaskMediaThumb,StepLogCheck,StepLogEvidence,TaskAttemptCard}`、`modules/dashboard/{DashboardView.style.css,components/ActivityTimeline.vue}`、`frontend/tests/check-dashed-whitelist.mjs`。
- 后端 / 接口 / 数据 / 交互逻辑：无改动。
