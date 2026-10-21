## 上下文

`TaskBoard`（523 行）是 `ai-assistant` 模块的私有组件，依赖同模块的 `useTaskList`、`useTaskPublish`、`constants`、`helpers/task-detail`、`helpers/task-device-address` 与 `api/tasks`。当前它直接挂在 `ai-assistant/index.vue` 的 `.doc-body` 里。侧栏导航由 `shared/components/sidebarNavConfig.ts` 的 `NAV_CATEGORIES` 驱动，`AppSidebar.isActive()` 对 `/ai-assistant` 使用前缀匹配。

## 目标 / 非目标

- 目标：新增独立 `/tasks` 任务清单页承载 `TaskBoard`；平台小助手页只留线路看板；侧栏 AI任务 分组按「任务清单、用例管理、测试报告」排序。
- 非目标：不把 `TaskBoard` 拆成新模块（会迫使跨模块 import 私有组件/组合式）；不改任务接口、任务卡字段、详情路由（仍 `/reports/task/:id`）；不改「测试报告」页的任务列表；不重命名「用例管理」。

## 决策

- 新页面 `TaskListPage.vue` 留在 `ai-assistant` 模块内，直接复用 `TaskBoard`。这样不触发模块边界红线，也不需要搬动 `api/tasks` 与任务常量。页面只是“新入口 + 新页头”，功能组件仍由任务域拥有。
- 路由选 `/tasks`，不选 `/ai-assistant/tasks`：`AppSidebar.isActive('/ai-assistant')` 会前缀匹配，若任务清单挂在 `/ai-assistant/tasks` 会导致「AI 助手」与「任务清单」同时高亮。`/tasks` 与既有 `/reports/task/:id`、`/ai-assistant/tasks/:taskId` 均不冲突。
- 侧栏「AI任务」顺序固定为 任务清单（`clipboard-list`）、用例管理（`layers`）、测试报告（`file-bar-chart`）；`MOD_COLORS` 为 `/tasks` 登记 `var(--c-ai)`，激活色与 AI 任务域一致。图标名必须落在 `shared/icons/lucide-registry.ts` 已登记子集内，`clipboard-list` 已登记。
- 新页面复用 `ai-workbench` 与 `index.style.css`，保持 AI 任务域的滚动与页头布局；页头 icon 用 `clipboard-list`，渐变沿用 AI teal。
- 平台小助手页删除 `TaskBoard` 与相关 import，页头副标题改为只描述线路/身份看板；`index.logic.ts` 的 `PAGE_HEADER.subtitle` 同步去掉“新建任务”。
- 仪表盘「任务数量」卡整卡跳转改为 `/tasks`；任务结果面板空态文案改为“前往任务清单新建”，避免指向已不承载任务列表的助手页。
- 保留 `TaskBoard` 区块标题「任务卡片」，页面标题「任务清单」；层级上页面 → 区块仍清晰。

## 风险 / 权衡

- 任务清单与测试报告都展示 AI 任务，但前者带新建/重跑/关闭/清空操作，后者是只读报告列表，职责不同；本次不合并两者。
- 旧路由 `/ai-assistant/tasks/:taskId` 仍注册但任务卡「详情」走 `/reports/task/:id`；这是既有行为，本次不动，避免扩大范围。
- 侧栏顺序由共享配置驱动，若后续再加 AI任务 子项，需要保持任务清单在首位。

## 迁移计划

- 纯前端页面拆分：新增组件与路由、移动模板区块、更新侧栏与入口链接。无数据迁移；回滚即还原新增文件与相关 import/配置。

## 开放问题

- 无。
