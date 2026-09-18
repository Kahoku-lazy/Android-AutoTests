## Why

element-locator 已完成项目化（`/elements/projects/:code`），旧的三域管理器页面在运行时**完全不可达**：`modules/element-locator/index.vue` 无任何路由或组件引用，其 `SECTION_BY_PATH` 映射的 `/elements/android|web|api` 三个路径已在 `routes.ts` 全部重定向。但该孤页仍挂着 3 个管理器（476/981/707 行）、3 棵树 composable（499/247/247 行）、1 个 667 行样式文件与 7 个只服务它们的测试文件，合计 4325 行。它们既拖累检索与阅读，又让"共享件的真实消费方"判断失真——`shared/components/GroupTreePanel.vue` 的唯一消费方正是这批死代码。在途变更 `refactor-element-locator-projects` 的剩余任务不含此项，故单独立项。

## What Changes

- **A 档 · 不可达页面（2892 行）**：移除 `modules/element-locator/index.vue`（71）、`components/ElementManager.vue`（476）、`components/ElementManager.css`（667）、`components/WebElementManager.vue`（981）、`components/ApiEndpointManager.vue`（707）
- **B 档 · 孤岛根部（1433 行）**：移除 `composables/useElementTree.ts`（499）、`composables/useWebGroupTree.ts`（247）、`composables/useApiGroupTree.ts`（247），以及只服务它们的 7 个测试文件（`tests/element-locator` 下 p0/p1 的 6 个 spec + `helpers/treeGroupFixtures.ts`），并移除随之变空的 `p1/`、`helpers/` 目录
- **文档同步（本次删除直接造成的失效引用）**：`modules/element-locator/AGENTS.md` 的"旧三域树"条目改述为"已删除 + 项目树为唯一树实现"；`tests/element-locator/p2/README.md` 移除两行失效条目
- **无 BREAKING**：不改变任何可达页面的行为；后端端点与数据表不动（`workflow` 仍读旧分组表）

## 关联文档

- 无 PRD/ARCH 关联：纯不可达代码删除 + 由删除直接造成的文档同步
- 在途变更 `refactor-element-locator-projects`（14/17）已完成路由与旧路径重定向（task 2.1）；其剩余任务为 3.3（dashboard 计数，可选）、4.2/4.3（验证），**不含本项**。本变更不修改该变更
- 后端约束：该变更 task 3.2 明确"workflow 仍可读旧分组表（未删表）"→ 本次只动前端

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯删除不可达代码与文档同步，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 删除 15 个文件 / 4325 非空行（A 2892 + B composable 993 + 测试 430）；移除 2 个空目录
- 修改 2 个文档：`frontend/src/modules/element-locator/AGENTS.md`、`frontend/tests/element-locator/p2/README.md`
- 可达页面行为零变化；`api.ts` **未裁剪**（27 个遗留函数属后续 C 档），因此 `tests/element-locator/p0/api.spec.ts` 原样保留且仍全绿（46/46）
- 遗留待决策（明确不在本变更）：`shared/components/GroupTreePanel.vue`（唯一消费方已随本次删除消失，但仍被规则列为"必用共享件"）、`shared/event-bus.ts`（唯一 src 消费方 useElementTree 已删）、`api.ts` 中 27 个只被遗留代码使用的函数（其中 5 个今天已无人使用）、`tests/PLAN-batch2-3modules.md` / `tests/DESIGN-batch2-3modules.md` 与 `GroupTreePanel.vue:4` 注释中的失效引用
