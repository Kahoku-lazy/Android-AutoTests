## 1. 盘点与备份

- [x] 1.1 列出全部 `AITask` / `AITaskAttachment` / `AITaskEvent` / `AITaskMedia` / `AIUsageHourly` 引用（apps、tests、scripts、前端），形成替换清单。验证：`rg` 清单与改动文件一一对应，无漏项。
- [x] 1.2 备份当前数据库，并在副本上演练表重命名与反向迁移。验证：副本迁移前后五张表行数一致，反向迁移可回到 `ai_*` 表名。

## 2. 后端 App 与模型迁移

- [x] 2.1 创建 `apps/task_list`，加入 `INSTALLED_APPS` 与 `config/urls.py`；模型 `Task` / `TaskAttachment` / `TaskEvent` / `TaskMedia` / `TaskUsageHourly`，表名 `task_*`，索引/约束沿用旧名。验证：`python manage.py check`；`makemigrations --check` 无未生成迁移。
- [x] 2.2 写 `ai_assistant` 迁移 A（`AlterModelTable` × 5）与迁移 B（state-only `DeleteModel` × 5），再写 `task_list` 初始 state-only `CreateModel` × 5。验证：在空库与有数据副本上 `migrate` 成功，五张表行数、外键、自增序列保持；反向迁移成功。
- [x] 2.3 任务 Admin 迁入 `task_list`；`ai_assistant` 不再注册任务 Admin。验证：Django Admin 任务页仍可读写，AI 助手 Admin 无任务模型。

## 3. 服务、接口与 URL

- [x] 3.1 迁移 `task_runner`、`engine_adapter`、`attachments`、`event_store`、`deepseek_billing`、`log_history`、上传清理与启动孤儿任务恢复到 `task_list`；启动恢复挂到 `task_list.AppConfig.ready`。验证：启动不报错；跑一条任务可完成；模拟 running 孤儿任务可恢复。
- [x] 3.2 迁移任务 views、serializers、urls 到 `/api/tasks/*`；旧 `/api/ai/tasks/*`、`/api/ai/agent-tasks/*` 不再注册。验证：新端点 200/4xx 正常；旧端点 404。
- [x] 3.3 任务详情聚合从 `report_generator/ai_task_reports.py` 拆出，`GET /api/tasks/{id}/report/` 接管；`/api/reports/task/{id}/` 下线。验证：详情页数据与旧响应字段一致；旧端点 404。
- [x] 3.4 更新 `dashboard`、`report_generator`、`ai_assistant` 的跨 App 引用到 `task_list` 模型/只读 api；`ai_assistant` 不再 import 任务。验证：`rg "AITask|AIUsageHourly|agent-tasks|tasks/submit" apps/ai_assistant` 无匹配；相关接口单测通过。

## 4. 前端任务清单模块

- [x] 4.1 新建 `frontend/src/modules/task-list/`，迁移 TaskBoard、TaskAttemptCard、StepLogEvidence、StepLogCheck、任务组合式、helpers、API 客户端与任务常量。验证：新模块可独立 build；无对 `ai-assistant` 私有任务文件的 import。
- [x] 4.2 新增 `/tasks` 与 `/tasks/:id` 路由，侧栏入口指向 `/tasks`；`ai-assistant` 路由/页面只保留助手与线路配置。验证：`/tasks` 列表、`/tasks/:id` 详情可访问；`/ai-assistant` 无任务区块。
- [x] 4.3 任务详情页由 `report-generator/TaskReport.vue` 迁入 `task-list/TaskDetailPage.vue`，API 改 `/api/tasks/{id}/report/`；测试报告列表、仪表盘、任务卡统一链到 `/tasks/:id`。验证：三处入口都进入 `/tasks/:id`；旧 `/reports/task/:id` 404/重定向到任务清单。
- [x] 4.4 前端 API 路径全部切到 `/api/tasks/*`；删除 `ai-assistant/api/tasks.ts` 与任务相关 helpers/常量。验证：`rg "/api/ai/(tasks|agent-tasks)|/api/reports/task" frontend/src` 无匹配。

## 5. 测试、spec 与关单

- [x] 5.1 后端测试迁移：模型导入、任务 API、事件、计费、dashboard/report 读取、迁移测试全部改到 `task_list`；新增表重命名行数/外键回归。验证：`pytest -m "unit or integration"` 相关集合通过。
- [x] 5.2 前端测试迁移：`TaskBoard`、`useTaskList`、`useTaskPublish`、`useTaskDetail`、任务详情、侧栏、路由测试全部改到新路径。验证：`npm test` 通过。
- [x] 5.3 文档与 spec 清扫：`apps/task_list/AGENTS.md`、`apps/ai_assistant/AGENTS.md`、`apps/report_generator/AGENTS.md`、根 `AGENTS.md` 表前缀、相关 OpenSpec specs 全部改到 `Task` / `task_*` / `/api/tasks/*` / `/tasks/:id`。验证：`rg "AITask|ai_tasks|/api/ai/agent-tasks|/reports/task" apps frontend openspec` 无残留（历史归档除外）。
- [ ] 5.4 本地门禁与迁移验收：`python manage.py check`、`makemigrations --check`、`ruff check`、`python run.py check`、前端 `npm run build:check`；在 MySQL/SQLite 副本各跑一次正向/反向迁移。验证：全部通过，五张表行数与备份一致。
  - 已完成：`manage.py check`、`makemigrations --check`、`ruff check`、`npm run build:check`；MySQL 备份副本正向/反向迁移通过，真实库 7 任务 / 44176 事件 / 176 媒体 / 13 小时用量行数一致。
  - 阻塞：`python run.py check` 仅剩非本任务文件（`engines/agents/role/base.py`、`assistant-cards.ts`）；SQLite 副本被既有 `ai_assistant.0021` 的 MySQL 专用 `ALTER COLUMN ... SET DEFAULT` 阻塞（非本次引入）。
