# task_list · 任务生命周期

> 归属模块：`backend/apps/task_list` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/task_list/urls.py`、`api.py`、`task_runner.py`、`engine_adapter.py`、`task_cost.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

- 拥有任务、附件、事件、媒体、小时用量五张表：
  `task_tasks` / `task_attachments` / `task_events` / `task_media` / `task_usage_hourly`。
- 提供 `/api/tasks/*`：提交、列表、详情、重跑、关闭、删除、清空、文件上传。
- **执行链**：`task_runner` → `engine_adapter` → `engines.backend_bridge`（模型与工具包全部由
  `engines.backend_bridge` 装配）；事件写 `event_store`。
- **计费**：`task_cost`（`engines/backend_bridge/model_billing/billing.py::DeepSeekBilling` 逐项对拍）
  → `TaskEventSink` 写事件 → `api.rollup_task_cost` 回写任务；用量落 `usage_ledger`。
  `deepseek_billing.py` 已退役为占位文件，**不要再引用**。
- **无报告端点**：任务详情报告端点已下线，`urls.py` 不再注册 `report` 路由；报告读取走
  `report_generator` 台账与 `ai_assistant` 的报告通道。
- **失败报告**：`failed` 且已进入执行（有事件记录）的任务必须留一份 HTML 报告，定位写入
  `Task.result` 的 `report_run` / `report_name`，任务清单与报告台账按该定位展示；
  `cancelled` 与 `interrupted` 不产报告；起跑前失败（无事件记录）只写失败原因。
- **创建人**：任务行下发 `created_by`（提交人用户 id，工作流提交时写入）与 `created_by_name`
  （读取时按 id 批量解析出的账号名）。解析不到时为空串，展示层显示「—」；不落库、不做迁移，
  账号改名后历史行跟随当前账号名。
- **失败收口用量**：`failed` 收口与成功收口一样，把本次运行已结束的模型调用写入逐次账
  （`source=task`、执行 ID 为任务号），并按执行 ID 回写任务的 token 与费用列；用量取整次运行
  的累计值覆盖写入，重复收口不翻倍。逐次账不可写时终态仍落库，费用可随后补汇总。
  `cancelled` 与 `interrupted` 不走本条，按各自既有口径处理。

## 红线

| 只做 | 禁止 |
|------|------|
| 任务域写操作经 `api.py` | 在 view/service 直写 ORM 绕过 `api.py` |
| 读 `ai_assistant.models.AssistantRelease` 与经 `ai_assistant.api` | import `ai_assistant` 的 views/service 内部实现 |
| 表名 `task_*`、索引/约束沿用旧名 | 新建第二套任务表或复制旧表数据 |

## 依赖方向

- `task_list` → `ai_assistant`：只读 `AssistantRelease` Model、经 `ai_assistant.api` 取智能体。
  （`AIAgent` / `filter_agents_for_user` / `resolve_assistant_name` 均已不存在。）
- `ai_assistant` → `task_list`：禁止。
- `dashboard` / `report_generator` → `task_list`：只读 Model 或 `task_list.case_identity` 纯函数，
  禁止 import views/service。（`task_reports.py` 已随 rework-test-report-inventory 退役。）

## 关单附加项

```
[ ] python manage.py check
[ ] makemigrations --check
[ ] python -m pytest -c tests/pytest.ini tests/task/api/test_task_*.py tests/task/unit/test_*task*.py
[ ] 旧 /api/ai/tasks/*、/api/ai/agent-tasks/* 返回 404
[ ] 迁移正向/反向均通过，五张表行数一致
```

全局关单清单见 `backend/AGENTS.md` §3。
