## 1. 迁出仍在用的两个格式化函数

- [ ] 1.1 新建 `frontend/src/modules/task-list/helpers/task-card.ts`，从 `task-detail.ts` **原样搬移** `formatTaskCost` 与 `formatTaskDuration`（含 docstring，不改逻辑）。验证：两函数体与搬移前逐字一致。
- [ ] 1.2 `frontend/src/modules/task-list/components/TaskBoard.vue` 的 import 改为 `from "../helpers/task-card"`，只导入这 2 个函数。验证：`npm run typecheck` 无 `Cannot find module`；`npm run test` 中 task-list 用例全绿。

## 2. 删除详情页装配代码

- [ ] 2.1 删除 `frontend/src/modules/task-list/helpers/task-detail.ts` 整文件（362 行）。验证：`task-detail` 在 `frontend/src` 内命中 0（`task-card.ts` 除外）；`typecheck` 通过。
- [ ] 2.2 删除 `frontend/src/modules/task-list/constants.ts` 的 `STEP_LOG_CHECK_TITLE` / `STEP_LOG_CHECK_HINT` / `STEP_LOG_CHECK_NO_SHOT_TEXT` 三个常量及注释。验证：三名字在 `frontend/src` 与 `frontend/tests` 命中 0。
- [ ] 2.3 删除 `frontend/src/shared/helpers/mediaUrl.ts` 与 `frontend/tests/shared/p0/mediaUrl.spec.ts`（详情模块删除后零引用，无 spec 点名）。验证：`mediaUrl` 在 `frontend/src` 与 `frontend/tests` 命中 0；`typecheck` 通过。

## 3. 清理测试

- [ ] 3.1 删除 `frontend/tests/task-list/p0/task-detail.spec.ts` 与 `frontend/tests/task-list/p0/planner-input-format.spec.ts`（被测函数已在第 2 组删除）。验证：`npm run test` 全绿，无 `Cannot find module`。
- [ ] 3.2 `frontend/tests/task-list/p0/datetime.spec.ts` 的 import 由 `@/modules/task-list/helpers/task-detail` 改为 `@/shared/helpers/datetime` 的 `formatIsoNaive`，**断言值一字不改**（保留「任务卡口径」注释）。验证：该文件 3 条断言全绿且与改动前期望值相同。
- [ ] 3.3 迁移 `formatTaskCost` / `formatTaskDuration` 的断言：新建 `frontend/tests/task-list/p0/task-card.spec.ts`，用例内容从 `task-detail.spec.ts` 的 `describe("formatTaskCost / formatTaskDuration")` 块原样搬移。验证：断言值逐字一致，`npm run test` 全绿。

## 4. 规格与文档

- [ ] 4.1 delta spec `specs/ai-task-list/spec.md` 已写明新口径（无详情入口、不跳 `/tasks/:id`），保留 3 个原场景名。验证：`openspec validate retire-task-detail-page --strict` 通过。
- [ ] 4.2 检查 `.agents/docs/frontend/task_list/**` 是否提到详情页或 `task-detail.ts`，有则同步。验证：`task-detail` / `/tasks/:id` 在 `.agents/docs/frontend/task_list/` 内命中 0 或已改为「该页已退役」。
- [ ] 4.3 本单 `.openspec.yaml` **不设** `skip_specs`（本单正是 spec 层变更）。验证：`openspec status --change retire-task-detail-page --json` 显示 specs 为 done 而非 skipped。

## 5. 门禁与关单

- [ ] 5.1 `npm run typecheck`、`npm run build`、`npm run lint:styles`、`npm run test` 四条 exit 0。验证：记录四条命令退出码。
- [ ] 5.2 用例数对比：删前基线（上一单关单为 92 文件 / 573 用例），说明减少量 = 删除的 2 个用例文件 + `mediaUrl.spec.ts`，新增 1 个 `task-card.spec.ts`。验证：差额可逐项对账。
- [ ] 5.3 关单汇报写明：`shared/types/ai.ts` 的 `TaskDetail*` / `TaskRun*` 类型**刻意保留**（对应既有接口 DTO，渲染层已不消费），接口若下线另开单删类型；随后归档。
