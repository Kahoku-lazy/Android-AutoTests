## Context

见 proposal.md 的 Why。行为以 `specs/agent-task-event-store/spec.md` 为准。`agent-event-fold` 已经把事件折成记录并交给接收方，默认接收方丢弃记录，引擎不写库。平台任务从 `apps/ai_assistant/task_runner.py` 进入 `run_platform_sop`。`engines` 不得 import `apps`。写库必须走 `apps/ai_assistant/api.py`。当前 `USE_TZ` 为 False，数据库不接受带时区的时间。

## Goals / Non-Goals

**Goals:**

- 任务线程内绑定平台接收方，把记录批量写入事件表，图片只留缩略图，模型调用结束累加小时用量。
- 任务结束或异常退出时刷出尾部记录，再只按模型调用结束行回写任务费用。
- 任务号为 0 时接收方直接返回，本地工作流和文本日志不改。

**Non-Goals:**

- 不提供事件、图片、用量的读接口，不改仪表盘和任务卡的 4 位费用展示。
- 不改 `apps/ai_assistant/deepseek_billing.py`，不保存原图，不做 90 天 / 30 天清理。
- 不用后台定时线程或 Celery 刷缓冲。

## Decisions

### D1：三张写入目标，任务费用加列

- `ai_task_events`：一条结构化记录一行。外键指向任务，删除任务时级联删除。`(task, seq)` 唯一。
- `ai_task_media`：只存缩略图。外键指向任务，级联删除。`(task, sha256)` 唯一。事件通过可空外键指向图片，删除图片时事件的引用置空。
- `ai_usage_hourly`：`(stat_date, stat_hour, model, role_name, agent_id)` 唯一。`agent_id` 为 `BigInteger`，默认 0，不设外键。
- `ai_tasks` 增加 `cost_input`、`cost_cache`、`cost_output`、`cost_total`，均为 `DECIMAL(14,8)`。

费用列统一 8 位，避免按次累加时把不足 0.0001 的金额收成 0。

备选：小时用量外键到智能体。否决。智能体删除不应挡住历史用量，未知智能体用 0 占位。

### D2：引擎只传上下文，平台接收方写库

`engines/agents/event_sink.py` 增加运行上下文：任务号、智能体号、用例标题、步骤序号、尝试次数。工作流在每条事件前扫描当前处于 running 或 awaiting 的步骤，盖上从 1 起的序号，以及该步已有验收次数加 1。没有这样的步骤时两项为空。

`apps/ai_assistant/event_store.py` 的接收方读取这个上下文。`task_runner` 在启动 SOP 前绑定接收方和上下文，在 `finally` 里关闭接收方并还原上下文。关闭失败只记日志，不改已经写出的任务终态。

备选：折叠模块直接写 ORM。否决。引擎会依赖 `apps`，也和「折叠不写库」冲突。

### D3：写入全部经 api.py

`insert_task_events`、`store_task_media`、`add_usage_hourly`、`rollup_task_cost` 放在 `apps/ai_assistant/api.py`。接收方只组行和压图，不直接 `bulk_create` 或 `save`。

序号在该任务已有最大序号之后递增。满 50 行写一次，关闭时再写剩余行。小时用量在事件插入成功之后累加，避免插入失败时重复计费。

任务费用只对 `event_type = ModelCallEndEvent` 求和。回复结束行可以带着本轮合计，但不能再加进任务列。

### D4：图片在任务线程里压缩略图

原图字节做 sha256。用 Pillow 转 RGB，长边缩到 720，JPEG 质量 80，只把缩略图 base64 入库。同一任务已有 40 张且哈希未见过时返回空引用。坏图跳过图片，事件照常写入。

备选：另起定时线程压图。否决。Django 连接不宜交给额外线程，取消任务时尾部也更容易丢。

### D5：调用时刻存成无时区的北京时间

带时区的结束时刻先换到 `Asia/Shanghai`，再去掉时区后写入。小时用量的日期和小时取这个时间。`is_peak` 取记录上计价快照里的 `peak`，没有快照时为空。

备选：打开 `USE_TZ` 再存带时区时间。否决。那会牵动全库时间字段，超出本变更。

### D6：折叠调用放到工作线程

`show()` 从正在运行的事件循环里被同步调用。接收方若在这条循环上查库，Django 会拒绝并只留下警告，事件不会入库。

工作流在盖上步骤号之后，用 `database_sync_to_async(..., thread_sensitive=False)` 把这一次 `show()` 放到工作线程。`thread_sensitive=False` 避免占用正在跑事件循环的那条线程。Django 未启动时仍在当前线程调用，引擎本地调试不连库。

## 模块防火墙自检

- 不新增跨 App import。接收方、任务线程和写入函数都在 `ai_assistant` 内。
- 引擎只增加上下文变量，不 import `apps`，也不 import 其它 App 的 service / runner。
- INSERT / UPDATE 都在 `apps/ai_assistant/api.py`。删除沿用任务删除，靠外键级联。
- 不改前端，仪表盘不写库。

## Risks / Trade-offs

- [事件插入成功后小时用量失败，重试会撞上唯一序号] → 插入成功后先清空缓冲再累加用量；用量失败只影响这一批的小时行，不重复插事件。
- [压图发生在插入之前，插入失败会留下未被事件引用的缩略图] → 图片仍属于该任务，删除任务时级联清掉；同一哈希再次出现会复用这一行。
- [40 张上限在并发写入时可能略超] → 一个任务只有一条运行线程，按当前计数判断即可。
- [正式库未执行迁移时，真实任务刷尾会因缺表报错] → 错误被任务线程记下，不改已写出的终态。发布前执行 `0058_task_event_store`。

## Migration Plan

迁移 `apps/ai_assistant/migrations/0058_task_event_store.py` 依赖 `0057_retire_agent_connectivity_check`。它给 `ai_tasks` 加四列费用，并创建事件表、图片表和小时用量表。已有任务的费用列默认为 0。

回滚时先停掉会写这些表的任务线程，再删除三张新表和四列费用。小时用量没有外键，可单独删。事件和图片随任务外键删除，不需要单独清历史任务。
