## 1. 表与迁移

- [x] 1.1 在 `apps/ai_assistant/models.py` 为任务增加四列 `DECIMAL(14,8)` 费用，并新增事件、缩略图、小时用量三个模型。事件与图片外键级联删除任务，小时用量的 `agent_id` 为裸整数且不设外键。验证：`python manage.py makemigrations ai_assistant --check --dry-run` 无新增差异。
- [x] 1.2 新增迁移 `0058_task_event_store`，依赖 `0057_retire_agent_connectivity_check`。验证：`python manage.py makemigrations ai_assistant --check --dry-run` 输出 `No changes detected`。

## 2. 写入入口

- [x] 2.1 在 `apps/ai_assistant/api.py` 增加批量插事件、按任务内 sha256 去重存缩略图（已有 40 张且不是重复图时返回空）、按唯一槽位累加小时用量、只对模型调用结束行回写任务费用。验证：`rg "bulk_create|objects.create|objects.update|\\.save\\(" apps/ai_assistant/event_store.py` 无匹配，写库只出现在 `api.py`。

## 3. 接收方与上下文

- [x] 3.1 在 `engines/agents/event_sink.py` 增加运行上下文的绑定、还原、读取，以及更新步骤序号和尝试次数。未绑定时任务号为 0。验证：`rg "import apps" engines/agents/event_sink.py` 无匹配。
- [x] 3.2 新增 `apps/ai_assistant/event_store.py`：任务号为 0 时丢弃；否则缓冲，满 50 行写入，关闭时刷尾再回写费用。图片在本线程压成 JPEG 缩略图。带时区的时刻先换到北京时间再去掉时区。小时用量在事件插入成功之后累加。验证：接收方模块不在引擎内直接写 ORM。

## 4. 接到任务运行

- [x] 4.1 `apps/ai_assistant/task_runner.py` 在启动 SOP 前绑定接收方和运行上下文，在 `finally` 里关闭接收方并还原。关闭失败只记日志。验证：阅读该函数，绑定发生在 `run_platform_sop` 之前，关闭发生在终态写入之后的 `finally`。
- [x] 4.2 `engines/agents/workflow/ui_auto_workflow.py` 在每条 `show()` 前，把处于 running 或 awaiting 的步骤序号和尝试次数写入上下文；没有这样的步骤时两项为空。验证：`rg "set_step_context" engines/agents/workflow/ui_auto_workflow.py` 有匹配，且仍调用 `AgentEventsShow.show`。

## 5. 收口

- [x] 5.1 新增 `tests/api/test_task_event_store.py`，覆盖序号与用例标题、步骤 2 尝试 1、模型调用的 8 位费用与小时用量、同一张图只存一行、40 张上限、任务号 0 不写库、删除任务带走事件和图片。验证：`python -m pytest tests/api/test_task_event_store.py -q` 通过。不改 `tests/engines/agents/test_agents_workflow.py`，不重跑真实模型。
- [x] 5.2 对改动路径跑 ruff，并跑 `python tools/gen_arch_stats.py --check-boundaries`。验证：ruff 通过，模块边界零违规。不跑全量回归。

## 6. 事件循环里不查库

- [x] 6.1 工作流在每条 `show()` 前盖上步骤后，用 `database_sync_to_async(..., thread_sensitive=False)` 把折叠和接收方放到工作线程。Django 未启动时仍在当前线程调用。验证：`tests/api/test_task_event_store.py` 增加一条在 `asyncio.run` 里调用 `show_event` 的用例，结束后能读到事件行；`python -m pytest tests/api/test_task_event_store.py -q` 通过。
