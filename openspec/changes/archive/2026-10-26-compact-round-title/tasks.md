## 1. 纯函数：标题拼装离开组件

- [x] 1.1 `frontend/src/modules/task-list/helpers/task-detail.ts`：新增 `roundKindLabel` 与 `roundTitleTail`（落地为 `roundTitleLead` / `roundTitleTail`：前段给「第 2 次 执行模型」，尾段给「：动作」，尾段无内容返回空串）。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：96 passed（13 个测试文件）。前段把重试次数与角色类别合成一处，免去模板里再判一次 `attempt`。
- [x] 1.2 `frontend/tests/task-list/p0/task-detail.spec.ts`：补三个断言——三类角色各得中文类别、未知角色回落执行模型、`第 2 次 验收模型` / `：启动 govee 应用` / 空串三种尾串。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：该文件 10 → 15 个用例，全过。
- [x] 1.3 新增 `frontend/tests/task-list/p0/task-detail-round-title.spec.ts`：挂载 `TaskDetailPage` 断言标题构成——行首数字序号保留、含「执行模型」、`executor_role` 为 `.badge-role` 徽章、标题不含「步骤」与 `deepseek-flash`、重试轮含「第 2 次」、`role` 为空时不出徽章。验证：`npx vitest run tests/task-list/p0/task-detail-round-title.spec.ts` 全绿。**验证结果**：4 passed。补这条的原因：1.1/1.2 只测纯函数，徽章是否真的渲染进标题只能靠挂载组件证明。

## 2. 组件：标题去掉重复序号与模型名，角色名改徽章

- [x] 2.1 `frontend/src/modules/task-list/TaskDetailPage.vue`：删掉 `STEP_CN`、`stepName()` 与 `roundTitle()`，改用 `roundTitleLead` / `roundTitleTail`；模板在类别后渲染 `role` 徽章，不再渲染 `round.model`。验证：`npm run typecheck` 通过，组件内无 `stepName` / `roundTitle` 残留。**验证结果**：`vue-tsc --noEmit` 退出码 0；`STEP_CN` / `stepName` / `roundTitle` 全仓无残留。
- [x] 2.2 `frontend/src/modules/task-list/TaskDetailPage.style.css`：新增 `.badge-role`（复用 `.badge` 基础样式，底色 `--paper`、字色 `--app-text-secondary`、`vertical-align: middle`、左间距 `--app-space-xs`），只用既有令牌与 `--app-size-xs`。验证：`npm run lint:styles` 通过。**验证结果**：样式门禁仍为改动前的 40 条存量告警（全部是 task-list 借用 `--ai-*` 模块令牌，与本文件无关），本条未新增；基线对比命令为 `git stash` 前后各跑一次 `node tests/check-style-gates.mjs`，计数一致。
- [x] 2.3 静态渲染复核：`temps/round-title-preview.html` + `temps/render-round-title.mjs` 用真实 `tokens.css` / `style.css` / `TaskDetailPage.style.css` 渲染宽屏与 380px 窄屏两种标题，确认徽章与 PASS/FAIL 同族、窄屏折行自然。验证：`temps/round-title-preview.png` 目视通过。**验证结果**：徽章垂直居中、窄屏折行不留半行空白（这就是 design.md 决策 1 要避开的 flex 子项效果）。

## 3. 门禁与页面验收

- [x] 3.1 前端门禁：`npm run typecheck` + `npx vitest run tests/task-list` + `npm run build` 全绿；仓库门禁 `python run.py check` 通过。验证：命令退出码 0。**验证结果**：typecheck / vitest（96 passed）/ vite build（17.5s）均过；`python run.py check` 阻塞项 21/22，唯一失败是 `openapi-schema`——它由工作区里先于本次的未提交后端改动引起（`backend/apps/accounts/*`、`backend/apps/task_list/*`、`openspec/openapi.yaml` 均为本次改动之前就已 `M` 的文件），本次前端改动不涉及 OpenAPI。
- [ ] 3.2 页面验收（用户侧，前端 dev server 已跑）：打开任一已跑完的任务详情，展开用例，确认轮次行为「序号 + 执行模型 + `executor_role` 徽章 + ：动作」，不含「步骤一」与 `deepseek-flash`；PASS/FAIL 徽章位置与样式未变。验证：用户目视确认。

## 4. 规格归档

- [x] 4.1 `openspec validate compact-round-title --strict` 通过；随后 `openspec archive compact-round-title`，主规格 `agent-task-flow-report` 的标题要求同步为新口径。验证：`openspec show agent-task-flow-report` 的该条需求不再要求中文步骤序号与模型名。**验证结果**：`validate --strict` 通过（首次因 MODIFIED 块漏保留既有场景「执行轮标题带动作」被拒，已按原名保留并改写 THEN）；归档后主规格该条需求改为「MUST NOT 出现中文步骤序号与模型名 + 角色名以徽章呈现」。
