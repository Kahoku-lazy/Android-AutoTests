## 1. 删除前引用核查

- [x] 1.1 `frontend/src` 全量搜索 14 个符号/导入前缀（`SSEMessageBuilder`、`useStorage`、`useRawStorage`、`wsUrl`、`ws-url`、`STEP_FIELDS`、`FIELD_LABELS`、`FIELD_HINTS`、`DIRECTION_OPTIONS`、`APP_LIFECYCLE_TYPES`、`MODULE_COLORS`、`module-colors`、`@/shared/sse`、`@/shared/constants`）→ 全部 **0 处**，确认无导入方
- [x] 1.2 仓库级搜索同一批符号 → 仅 4 处**文档**提及（无代码引用）：`dev_docs/项目笔记/1.md:78,167`、`dev_docs/03-设计与架构/技术栈参考.md:160`、`frontend/tests/PLAN-batch2-3modules.md:497`；验证 `tools/frontend-whitelist.json` / `tools/boundary-whitelist.json` 未登记这些路径

## 2. 删除

- [x] 2.1 删除 `frontend/src/shared/sse/SSEMessageBuilder.ts`（306 行），并移除空目录 `frontend/src/shared/sse/`；验证目录不再存在
- [x] 2.2 删除 `frontend/src/shared/composables/useStorage.ts`（66 行）；验证文件不再存在
- [x] 2.3 删除 `frontend/src/shared/ws-url.ts`（6 行）；验证文件不再存在
- [x] 2.4 删除 `frontend/src/shared/constants/steps.ts`（73 行）与 `frontend/src/shared/constants/module-colors.ts`（13 行），并移除空目录 `frontend/src/shared/constants/`；验证目录不再存在

## 3. 门禁验证

- [x] 3.1 删除后重跑同一批符号搜索 → 全部 **0 处**，确认无悬空导入
- [x] 3.2 前端类型检查 `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`（workdir: frontend）→ 共 50 行输出，**提及被删文件/符号的 0 行**；其余报错均为既有类型债（`ProjectTree.vue`、`device-inspector/store.ts`、`tests/dashboard/*`），判定删除未引入类型错误
- [x] 3.3 `git status --porcelain -- frontend/src/shared` → 恰好 5 个 `D` 条目，无其他改动混入本次删除
- [x] 3.4 未删除项确认（防误伤）：`AnimatedMenuIcon.vue` 已写入 `frontend/AGENTS.md` 侧边栏清单，保留待用户决策；`tokens.css` 的 4 个 `--app-sidebar-*` 令牌与 `types/ai.ts` 的 `ConnectionMode` 明确不在本次范围
