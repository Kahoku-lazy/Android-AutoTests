## 1. 删除前核实

- [x] 1.1 全仓库引用核实 → `element-locator/index.vue` **0 处**源码引用（唯一命中是 `router.ts:9` 注释）；三个 Manager 各仅被该孤页 import + 渲染 1 处；三个 composable 仅被对应 Manager 引用
- [x] 1.2 可达性核实 → `routes.ts:23-33` 中 `/elements/android|web|api` 与 `/element-mgr` 全部 redirect 到 `/elements/projects/{code}`；孤页的 `SECTION_BY_PATH` 三个 key 均已失效，即使挂路由也取不到 activeKey
- [x] 1.3 二级连带盘点 → `GroupTreePanel.vue` 唯一消费方 = 两个 Manager；`shared/event-bus.ts` 唯一 src 消费方 = `useElementTree`；`api.ts` 27 个函数只被遗留代码使用 → 全部归 C 档，本次**不动**
- [x] 1.4 计划核对 → 在途变更 `refactor-element-locator-projects` 剩余任务不含本项，无重复/冲突

## 2. A 档 · 删除不可达页面（2892 行）

- [x] 2.1 删除 `modules/element-locator/index.vue`（71 行）；验证文件不存在
- [x] 2.2 删除 `components/ElementManager.vue`（476）与 `components/ElementManager.css`（667）
- [x] 2.3 删除 `components/WebElementManager.vue`（981）与 `components/ApiEndpointManager.vue`（707）
- [x] 2.4 验证 `components/` 仅剩可达页面的组件（LocatorFilePanel / LocatorTree / PageElementsWorkbench / PageScreenshotOverlay）

## 3. B 档 · 删除 composable 与专属测试（1433 行）

- [x] 3.1 删除 `composables/useElementTree.ts`（499）、`useWebGroupTree.ts`（247）、`useApiGroupTree.ts`（247）
- [x] 3.2 删除 6 个 spec（p0/p1 × useElementTree 88/99、useWebGroupTree 21/43、useApiGroupTree 21/43）与 `helpers/treeGroupFixtures.ts`（115）
- [x] 3.3 移除变空目录 `tests/element-locator/p1/`、`tests/element-locator/helpers/`
- [x] 3.4 保留 `tests/element-locator/p0/api.spec.ts`（它覆盖 `api.ts`，而 api.ts 属 C 档未动）

## 4. 文档同步（删除直接造成的失效引用）

- [x] 4.1 `modules/element-locator/AGENTS.md`：旧三域树条目改述为"已删除；项目树 `useLocatorTree` 为唯一树实现，禁止再引入第二棵树"
- [x] 4.2 `tests/element-locator/p2/README.md`：移除 "ElementManager.vue 整页 mount" 与 "三树同构重构" 两行

## 5. 门禁验证

- [x] 5.1 残留引用搜索（7 个符号，src + tests）→ `frontend/src` 仅剩 `GroupTreePanel.vue:4` 注释与模块 AGENTS.md 的"已删除"说明；`frontend/tests` 仅剩 `PLAN-batch2-3modules.md` / `DESIGN-batch2-3modules.md` 计划文档（已登记为待决）
- [x] 5.2 `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`（workdir: frontend）→ 37 条错误全部落在 7 个无关文件（`tests/dashboard/*`、`device-inspector/store.ts`、`case-manager/components/ProjectTree.vue`、`tests/ai-assistant/p0/TaskAttemptCard.spec.ts`），**提及被删文件的 0 条**。错误数较前次 +2 来自用户新加入的 `TaskAttemptCard.spec.ts`，与本变更无关
- [x] 5.3 `node node_modules/vitest/vitest.mjs run tests/element-locator` → **46/46 通过**（仅剩 api.spec.ts）。注：该命令在受限沙箱下会因 Vite 内部 realpath 子进程 `spawn EPERM` 失败，已按沙箱规范单次升级权限后执行成功
- [x] 5.4 `git status` → 本变更恰好 15 个 `D` + 2 个 `M`（模块 AGENTS.md、p2/README.md），无其他改动混入
