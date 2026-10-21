# task_list App AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `apps/AGENTS.md` 优先于本文件。

## 职责

- 拥有任务、附件、事件、媒体、小时用量五张表：`task_tasks` / `task_attachments` / `task_events` / `task_media` / `task_usage_hourly`。
- 提供 `/api/tasks/*`：提交、列表、详情、重跑、关闭、删除、清空、详情报告、文件上传。
- 执行链：`task_runner` → `engine_adapter` → 引擎；事件写 `event_store`；计费 `deepseek_billing`。

## 红线

| 只做 | 禁止 |
|------|------|
| 任务域写操作经 `api.py` | 在 view/service 直写 ORM 绕过 `api.py` |
| 读 `ai_assistant.AIAgent` 与只读 `api.py` | import `ai_assistant` 的 views/service/task 页面 |
| 表名 `task_*`、索引/约束沿用旧名 | 新建第二套任务表或复制旧表数据 |

## 依赖方向

- `task_list` → `ai_assistant`：只读 `AIAgent`、`filter_agents_for_user`、`resolve_assistant_name`。
- `ai_assistant` → `task_list`：禁止。
- `dashboard` / `report_generator` → `task_list`：只读 Model 或 `task_list.task_reports`，禁止 import views/service。

## 关单附加项

```
[ ] python manage.py check
[ ] makemigrations --check
[ ] pytest tests/api/test_task_*.py tests/graybox/unit/test_*task*.py
[ ] 旧 /api/ai/tasks/*、/api/ai/agent-tasks/* 返回 404
[ ] 迁移正向/反向均通过，五张表行数一致
```
