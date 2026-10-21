## 上下文

当前任务域与 AI 助手共用 `apps/ai_assistant`：

- 模型：`AITask`、`AITaskAttachment`、`AITaskEvent`、`AITaskMedia`、`AIUsageHourly`，表名 `ai_tasks` / `ai_task_attachments` / `ai_task_events` / `ai_task_media` / `ai_usage_hourly`。
- 接口：`/api/ai/tasks/submit/`、`/api/ai/agent-tasks/*`、`/api/ai/upload-file/`。
- 服务：`task_runner`、`engine_adapter`、`attachments`、`event_store`、`deepseek_billing`、`log_history`、启动时孤儿任务恢复。
- 前端：任务卡片、发布弹窗、任务详情、日志证据都在 `ai-assistant` 模块；任务详情页在 `report-generator` 的 `/reports/task/:id`。
- 消费方：`dashboard` 读 `AITask` / `AIUsageHourly`；`report_generator` 读 `AITask` / `AITaskEvent` / `AITaskAttachment`。

## 目标 / 非目标

- 目标：任务域成为独立后端 App + 独立前端模块；`ai_assistant` 只保留 `AIAgent`、线路/身份配置、`/api/ai/agents/*`、头像上传。
- 目标：任务表改名为 `task_*`，数据零丢失、迁移可回滚。
- 目标：任务详情页与详情聚合迁入任务清单 `/tasks/:id`。
- 非目标：不改任务执行引擎、SOP 流程、设备调度算法本身；不改测试报告列表的只读聚合口径；不做旧 URL 兼容别名（产品已确认下线）。

## 目标结构

```
apps/task_list/
  models.py            Task / TaskAttachment / TaskEvent / TaskMedia / TaskUsageHourly
  migrations/          表重命名 + 状态迁移
  api.py               任务写操作与只读查询（供 dashboard/report 复用）
  views_drf.py         任务提交/列表/详情/重跑/关闭/删除/清空/报告
  urls.py              /api/tasks/*
  task_runner.py       执行线程
  engine_adapter.py    引擎请求装配
  attachments.py       附件解析与存储
  event_store.py       事件写入
  deepseek_billing.py  任务计费
  log_history.py       任务日志
  apps.py              启动孤儿任务恢复
  admin.py             任务 Admin

frontend/src/modules/task-list/
  index.vue            /tasks 列表
  TaskDetailPage.vue   /tasks/:id 详情（由 report-generator/TaskReport.vue 迁入）
  routes.ts
  api/tasks.ts
  components/          TaskBoard / TaskAttemptCard / StepLogEvidence / StepLogCheck
  composables/         useTaskList / useTaskPublish / useTaskDetail
  helpers/             task-detail / task-device-address / log-evidence / yaml-case-titles
  constants.ts         任务状态、筛选、分组
```

`ai_assistant` 保留 `AIAgent`、`AgentRouteCard`、`AgentDetail`、`api/agents`、`helpers/assistant-cards`、`model-capability`、头像上传、`/api/ai/agents/*`、`/api/ai/upload-avatar/`。不得 import `task_list`。

## 数据迁移

Django 不支持直接把模型状态从一个 app 挪到另一个 app，采用「先改名、再拆状态」三支迁移：

1. `ai_assistant` 迁移 A：对 5 个模型执行 `AlterModelTable`，把表改名为 `task_tasks` / `task_attachments` / `task_events` / `task_media` / `task_usage_hourly`；保留全部行、外键与索引。
2. `ai_assistant` 迁移 B：`SeparateDatabaseAndState(database_operations=[], state_operations=[DeleteModel(...) × 5])`，只撤状态，不删表。
3. `task_list` 初始迁移：`SeparateDatabaseAndState(database_operations=[], state_operations=[CreateModel(...) × 5])`，依赖迁移 B；`Task.agent` 外键指向 `ai_assistant.AIAgent`，`TaskEvent.media` 指向 `TaskMedia`。

要点：

- 新模型沿用原索引/约束名（`idx_evt_task_seq`、`uk_evt_task_seq` 等），避免数据库与模型状态出现第二套名字。
- 自增序列、外键约束由表重命名保留；SQLite/MySQL 必须各跑一次迁移演练并核对行数。
- 回滚顺序：反向 `task_list` 初始迁移 → 反向 `ai_assistant` B → 反向 A（表名改回）。
- 迁移前必须备份；迁移脚本不复制行、不做数据变换。

## API 映射

| 旧 | 新 |
|---|---|
| `POST /api/ai/tasks/submit/` | `POST /api/tasks/submit/` |
| `GET /api/ai/agent-tasks/` | `GET /api/tasks/` |
| `GET /api/ai/agent-tasks/{id}/` | `GET /api/tasks/{id}/` |
| `POST /api/ai/agent-tasks/{id}/rerun/` | `POST /api/tasks/{id}/rerun/` |
| `POST /api/ai/agent-tasks/{id}/cancel/` | `POST /api/tasks/{id}/cancel/` |
| `POST /api/ai/agent-tasks/{id}/delete/` | `POST /api/tasks/{id}/delete/` |
| `POST /api/ai/agent-tasks/clear/` | `POST /api/tasks/clear/` |
| `POST /api/ai/upload-file/` | `POST /api/tasks/upload-file/` |
| `GET /api/reports/task/{id}/` | `GET /api/tasks/{id}/report/` |

任务接口保持 `{status, data}` 信封；`/api/reports` 列表仍是既有平铺信封，不改。

## 依赖方向

- `task_list` → `ai_assistant`：只读 `AIAgent` 与 `filter_agents_for_user` / `resolve_assistant_name`，走对方 `api.py` / Model。
- `ai_assistant` → `task_list`：禁止。
- `dashboard` / `report_generator` → `task_list`：读 Model 或只读 `api.py`，禁止 import views/service。
- 前端 `ai-assistant` → `task-list`：禁止；`task-list` 可复用 shared 组件。

## 风险 / 权衡

- 表重命名 + 状态迁移是本次最高风险项：迁移脚本必须可逆、必须在备份副本上演练；任何一步失败回滚到旧表名。
- 旧 URL 下线是破坏性变更；仓库内所有调用方（前端、测试、脚本）必须一次性切换，不能留半套。
- `report_generator` 的任务详情聚合迁出后，测试报告列表仍要读任务表；需避免它反向依赖 `task_list` 的 service。
- 启动时孤儿任务恢复线程要从 `ai_assistant.AppConfig` 移到 `task_list.AppConfig`，否则 `AITask` 状态移除后启动即报错。
- 任务详情页从 `report-generator` 迁出后，测试报告列表、仪表盘、任务卡三处链接必须统一到 `/tasks/:id`。
- 大量测试与 spec 引用旧模型/旧路径，需要机械替换后逐项跑通；不做「旧路径兼容」可以暴露遗漏。

## 迁移计划（分阶段）

1. 盘点与冻结：列出所有 `AITask` / 任务 API / 任务组件引用；备份数据库；在副本上演练表重命名。
2. 后端拆 App：建 `apps/task_list`、搬模型与服务、写三支迁移；跑 `migrate` / 反向迁移 / 行数核对。
3. 后端接口：搬 views/urls，下线旧路径；改 dashboard、report_generator、启动恢复、admin。
4. 前端拆模块：建 `modules/task-list`，搬组件/组合式/API/helpers，改路由、侧栏、链接。
5. 详情迁移：`TaskReport.vue` → `TaskDetailPage.vue`，后端详情聚合同步迁入 `/api/tasks/{id}/report/`。
6. 清理与验收：删 `ai_assistant` 任务残留、统一 spec/AGENTS、跑全量相关测试与 CI。

## 开放问题

- 无。表前缀采用新 `task_`，需同步根 `AGENTS.md` 的前缀清单。
