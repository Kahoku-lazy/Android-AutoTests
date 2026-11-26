## 1. 迁出仍在用的两个格式化函数

- [x] 1.1 新建 `frontend/src/modules/task-list/helpers/task-card.ts`，从 `task-detail.ts` **原样搬移** `formatTaskCost` 与 `formatTaskDuration`（逻辑一字不改，**不写注释**）。验证：两函数体与搬移前一致；文件内无注释。
- [x] 1.2 `frontend/src/modules/task-list/components/TaskBoard.vue` 的 import 改为 `from "../helpers/task-card"`。验证：`npm run typecheck` 无 `Cannot find module`。

## 2. 删除详情页装配代码

- [x] 2.1 删除 `frontend/src/modules/task-list/helpers/task-detail.ts` 整文件。验证：`task-detail` 在 `frontend/src` 内命中 0；`typecheck` 通过。
- [x] 2.2 删除 `frontend/src/modules/task-list/constants.ts` 的 `STEP_LOG_CHECK_TITLE` / `STEP_LOG_CHECK_HINT` / `STEP_LOG_CHECK_NO_SHOT_TEXT`。验证：三名字在 `frontend/src` 与 `frontend/tests` 命中 0。
- [x] 2.3 删除 `frontend/src/shared/helpers/mediaUrl.ts` 与 `frontend/tests/shared/p0/mediaUrl.spec.ts`。验证：`mediaUrl` 在 `frontend/src` 与 `frontend/tests` 命中 0；`typecheck` 通过。

## 3. 清理与迁移测试

- [x] 3.1 删除 `frontend/tests/task-list/p0/task-detail.spec.ts` 与 `frontend/tests/task-list/p0/planner-input-format.spec.ts`。验证：`npm run test` 全绿，无 `Cannot find module`。
- [x] 3.2 新建 `frontend/tests/task-list/p0/task-card.spec.ts`，把原 `task-detail.spec.ts` 里 `formatTaskCost` / `formatTaskDuration` 的断言**原样搬入**（断言值一字不改，**不写头部注释**）。验证：`npx vitest run tests/task-list/p0/task-card.spec.ts` 全绿，断言值与搬移前逐字相同。

## 4. 规格与文档

- [x] 4.1 delta spec 已写明新口径（无详情入口、不跳 `/tasks/:id`），保留 3 个原场景名。验证：`openspec validate retire-task-detail-page --strict` 通过。
- [x] 4.2 检查 `.agents/docs/frontend/task_list/**` 是否提到详情页或 `task-detail.ts`，有则同步。验证：`task-detail` 与 `/tasks/:id` 在该目录内命中 0 或已改为「该页已退役」。
- [x] 4.3 本单 `.openspec.yaml` **不设** `skip_specs`。验证：`openspec status --change retire-task-detail-page --json` 显示 specs 为 done。

## 5. 门禁与关单

- [x] 5.1 `npm run typecheck`、`npm run build`、`npm run lint:styles`、`npm run test` 四条 exit 0。验证：记录退出码。
- [x] 5.2 用例数对比：记录 apply 前基线与 apply 后数量，说明差额 = 删 2 个用例文件 + `mediaUrl.spec.ts`，新增 `task-card.spec.ts`。验证：差额可逐项对账。
- [x] 5.3 关单汇报写明：`TaskDetail*` / `TaskRun*` 类型刻意保留（对应既有接口 DTO）、新文件无注释符合新规则。随后归档。
