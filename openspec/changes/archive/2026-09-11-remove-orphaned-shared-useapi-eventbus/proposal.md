## Why

上一轮删除 element-locator 遗留管理器后，两个 shared 文件失去了全部消费者：`composables/useApi.ts` 仅有的两个使用者（`ApiEndpointManager.vue`、`useApiGroupTree.ts`）与 `event-bus.ts` 的唯一使用者（`useElementTree.ts`）都已随该变更删除。两者共 55 行，经精确搜索确认已零引用，属可无风险清退的死代码。

## What Changes

- 删除 `frontend/src/shared/composables/useApi.ts`（53 行，0 消费方）
- 删除 `frontend/src/shared/event-bus.ts`（2 行，0 消费方）
- **无 BREAKING**：无导入方、无运行时行为变化、无 API/依赖变更

## 关联文档

- 无 PRD/ARCH 关联：纯死代码清退（C1 档），承接变更 `2026-09-11-remove-legacy-element-locator-managers` 的连带影响
- 遗留文档提及（本次不改，仅登记）：`frontend/tests/PLAN-batch2-3modules.md:235,240,248`（旧计划）；`dev_docs/03-设计与架构/技术栈参考.md:159`（目录树）；`.agents/skills/architecture-review/references/analysis-checklist.md:21`（检查项 grep `event-bus`，删除后该检查恒为通过）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯死代码清退，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 删除 2 个文件 / 55 非空行；`shared/composables/` 由 9 个减为 8 个
- 零行为变化；前端类型检查 35 条既有错误不变，其中提及被删文件的 **0 条**
- C2（`animations.ts` 24 个未用函数、`icons/index.ts` 23 个未用图标）与 C3（单模块件下沉）明确不在本变更
