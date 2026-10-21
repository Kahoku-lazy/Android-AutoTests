## Why

「平台小助手」页同时承载线路看板与任务卡片，任务入口被埋在助手页里；侧栏「AI任务」分组只有用例与报告，没有任务入口。产品要求把任务卡片功能拆成独立的「任务清单」页，并在侧栏 AI任务 分组中与用例、报告并列。

## What Changes

- 新增 `/tasks`「任务清单」页，承载原「平台小助手」页的任务卡片区块（筛选、状态分组、新建任务、调试清空、卡片列表、重跑/关闭/详情）。
- 「平台小助手」页移除任务卡片区块，只保留助手线路/身份看板；页头副标题同步去掉任务相关文案。
- 侧栏「AI任务」分组按顺序提供：任务清单（`/tasks`）、用例管理（`/cases`）、测试报告（`/reports`）。
- 仪表盘「任务数量」卡片的整卡跳转目标从 `/ai-assistant` 改为 `/tasks`；任务结果面板空态文案改为指向任务清单。
- 接口、任务提交/重跑/关闭/清空契约与详情路由不变。

## 关联文档

- PRD-01 仪表盘（任务卡片入口）
- PRD-08 AI 助手（助手看板与任务卡片）

## Capabilities

### New Capabilities

- `ai-task-list`: 任务清单页的承载内容、任务卡字段与侧栏入口顺序

### Modified Capabilities

- `dashboard-agent-tasks`: 任务结果面板空态文案指向任务清单；原「助手页任务卡仅标题与详情」要求移到 `ai-task-list`
- `dashboard-chapter-boards`: 「任务数量」卡的整卡跳转目标改为任务清单页

## Impact

- 新增 `frontend/src/modules/ai-assistant/TaskListPage.vue`
- `frontend/src/modules/ai-assistant/index.vue`、`index.logic.ts`：移除任务卡片区块与任务相关页头文案
- `frontend/src/modules/ai-assistant/routes.ts`：新增 `/tasks` 路由
- `frontend/src/shared/components/sidebarNavConfig.ts`：新增侧栏入口、顺序与模块色
- `frontend/src/modules/dashboard/index.vue`、`components/TaskResultPanel.vue`：任务入口与空态文案
- `frontend/src/modules/ai-assistant/AGENTS.md`：模块布局说明
- `frontend/tests/`：侧栏顺序与路由单测
- 后端接口与数据模型不变
