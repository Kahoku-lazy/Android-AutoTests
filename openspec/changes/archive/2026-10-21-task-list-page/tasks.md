## 1. 任务清单页

- [x] 1.1 新增 `TaskListPage.vue`：页头「任务清单」，`ai-workbench` 布局，正文承载 `TaskBoard`。验证：文件存在，页头标题与区块标题渲染正确。
- [x] 1.2 新增 `/tasks` 路由（name `ai-task-list`、meta.title「任务清单」），并确认不与 `/reports/task/:id`、`/ai-assistant/tasks/:taskId` 冲突。验证：`aiRoutes` 含该路由，浏览器直接访问 `/tasks` 可进入。
- [x] 1.3 从 `ai-assistant/index.vue` 移除 `TaskBoard` 及 import，页头副标题去掉任务相关文案；同步 `index.logic.ts` 的 `PAGE_HEADER.subtitle`。验证：平台小助手页不再出现任务卡片区块或「新建任务」，`rg "TaskBoard" index.vue` 无匹配。

## 2. 侧栏与入口

- [x] 2.1 侧栏「AI任务」分组按顺序新增 任务清单（`/tasks`）、用例管理（`/cases`）、测试报告（`/reports`）；`MOD_COLORS` 增加 `/tasks`。验证：侧栏顺序与文案正确，`/tasks` 激活时「AI 助手」不同时高亮。
- [x] 2.2 仪表盘「任务数量」卡 `path` 改为 `/tasks`；任务结果面板空态文案改为「暂无任务卡片，前往任务清单新建」。验证：`rg "/ai-assistant" index.vue` 不再命中任务数量卡；空态文案正确。

## 3. 文档与测试

- [x] 3.1 更新 `ai-assistant/AGENTS.md`：平台小助手页只保留线路看板，任务卡片列表迁至 `/tasks` 任务清单页。验证：文档不再把 TaskBoard 列为助手页第二区块。
- [x] 3.2 新增侧栏顺序与 `/tasks` 路由单测。验证：`npx vitest run tests/shared/p1/sidebarNavConfig.spec.ts tests/ai-assistant/p1/task-list-route.spec.ts` 通过。
- [x] 3.3 仪表盘与 AI 助手相关单测通过：`npx vitest run tests/ai-assistant/p0/useTaskList.spec.ts tests/dashboard/p0/StatsCard.spec.ts tests/dashboard/p1/DashboardView.logic.spec.ts`。
- [x] 3.4 前端类型检查与构建通过：`npm run build:check`。
- [x] 3.5 运行前端门禁 `vue-frontend-check`；浏览器验证 `/tasks`、平台小助手页与仪表盘任务数量卡跳转。
- [x] 3.6 归档前同步 `dashboard-agent-tasks` 主 spec 的 Purpose，并确认 `openspec validate "2026-10-21-task-list-page" --strict` 通过。
