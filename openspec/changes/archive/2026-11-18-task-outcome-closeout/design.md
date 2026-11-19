## Context

任务终态现在有两条互不相让的写路径。`run_task_async` 把未接住的异常写成纯文本 `执行异常` 并标 `failed`，同时整段替换 `Task.result`。`recover_orphaned_tasks` 在服务启动时把全部 `running` 改成 `interrupted`，说明固定为服务重启。取消优先只做在成功路径的 `refresh_from_db` 上，异常路径会把已经写成的 `cancelled` 盖掉。

开发后端由 `run_daphne.py` 的 autoreload 拉起。子进程只有 `RUN_MAIN=true`，第一次启动和热重载无法区分。`python run.py stop` 会先排空，最多等 180 秒，超时才杀进程；这条路径是唯一能在杀进程前知道「是停机超时」的地方。

`BudgetExceeded` 与 `RunCancelled` 都继承 `RuntimeError`，但中间件约定把预算超限记成中止，不记成失败。报告通过率只把 `failed` 计入失败。动机见 `proposal.md`。

## Goals / Non-Goals

**Goals:**

- 终态写入变成条件更新：只有当前行仍是 `running` 才能改状态和结果。
- 失败和中断的原因放进同一份 JSON，保留 `workflow_id`。
- 用心跳把「旧进程还在跑」和「进程已经没了」分开，清扫可以重复跑。
- 停机超时在杀进程前留下任务编号，下次写成 `stop_timeout`。

**Non-Goals:**

- 不新增 `TaskStatus` 值，不为热重载单独做探测。
- 不自动重试模型 400、超时或设备命令。
- 不改报告通过率分母，不改清单上的「任务失败 / 已中断」标签。
- 不保证抛错时一定还有完整 HTML 报告。`run_sop` 在 `finish` 之前抛错时，磁盘上可能只有半截 jsonl。
- 不改助手测试对话的状态口径。对话表现在把异常记成 `interrupted`，与任务清单相反；对齐需要另立变更。

## Decisions

**D1 条件更新是唯一收口。** 新增 `claim_terminal(task_id, status, result, usage, costs)`，内部是 `UPDATE ... WHERE id=? AND status='running'`。影响行数为 1 才算终态生效，并在此时登记 BUG、按设备拉起下一条。影响行数为 0 时，若调用方带了用量，只补 token 和费用字段，不改 `status` 和 `result`。`finalize_task` 的成功、失败、取消、中断都走这一条。备选是继续 `refresh_from_db` 再保存：两个线程可以都读到 `running`，后写的覆盖先写的。否决。

**D2 结果只合并。** 读出当前 `result`。能解析成对象就保留 `workflow_id` 以及其它已有键，再写入本次的 `failure_kind` 或 `cause`、`reason`、`status`。解析失败时新对象仍尽量从任务附件或提交记录找回 `workflow_id`；找不到就省略，不把纯文本异常写回去。列表摘要继续走 `task_result_preview`，优先 `reason`，其次中断说明，最后才是旧的 `summary`。

**D3 失败类别只在一个 except 里分。** `verdict` 只来自步骤结论，不来自异常。异常分类：

| 类型 | failure_kind | reason |
| --- | --- | --- |
| OpenAI / httpx 的 4xx、超时、连接错误 | `provider` | `模型拒绝（{状态码}）` 或 `模型网关不可用` |
| `AdbError` | `device` | `设备命令失败` |
| `BudgetExceeded` | 不进失败；`cause=budget`，状态 `interrupted` | `运行超出预算` |
| `RunCancelled` | 状态 `cancelled` | 已有关闭说明则不改 |
| 其它，含 `ValueError`、`SynchronousOnlyOperation` | `platform` | `平台执行错误（{异常类名}）` |

不新增自定义异常。堆栈只留 `backend_log.exception`，不进 `result`。备选是按异常消息关键词分类：网关文案一变就分错。否决。

**D4 心跳由旁路线程写，不进事件循环。** `Task` 增加可空的 `heartbeat_at`。工作线程在 `start_task` 后启动一个 daemon 定时器，每 15 秒执行 `UPDATE task_tasks SET heartbeat_at=now WHERE id=? AND status='running'`。`finally` 里取消定时器。这样模型调用堵住时心跳仍在，清扫不会收走活任务。备选是在每次模型返回后写心跳：调用挂起超过阈值就会被误收。否决。

**D5 清扫替代只跑一次的启动恢复。** 阈值 45 秒，间隔 30 秒。只处理 `status='running' AND (heartbeat_at IS NULL OR heartbeat_at < now-45s)`。`heartbeat_at` 为空是旧数据或线程还没写出第一拍，同样视为超时，避免漏收。清扫写 `interrupted`，`cause` 先查停机名单，在名单里则 `stop_timeout`，否则 `process_lost`。然后对涉及设备调用现有 `dispatch_device`。只在 ASGI 服务进程启动，沿用 `DJANGO_ASGI_SERVER` / daphne / runserver 判断，并跳过 `DJANGO_AUTORELOAD_PARENT=1` 的父进程。管理命令和测试不跑。启动时立刻跑一轮，避免只靠定时器。备选是继续只在 `ready()` 收一次：昨天启动恢复自己失败时，遗留任务会一直停在 `running`。否决。

**D6 停机名单是一次进程的侧写，不是新状态。** `run.py` 在排空超时、调用 `kill_port` 之前，向本机 drain 接口再取一次仍为 `running` 的任务编号，写入 `temps/stop-timeout-tasks.json`（只含编号列表和写入时间）。下次清扫读到就按编号套用，用过后删除该文件。后端不可达时写不出名单，这些任务按 `process_lost` 收，这是可接受的降级：状态仍是中断，只是原因粗一点。不把名单放进数据库新表。备选是环境变量传递：杀进程后子进程看不到。否决。

**D7 BUG 来源键按类别，不按每次收口。** `verdict` 继续用 `case:{用例}`，空列表用 `task`。`provider` / `device` / `platform` 用 `task:provider`、`task:device`、`task:platform`。中断仍用 `task`，正文改为 `cause` 对应的一句说明。唯一约束已有 `(task_id, category, source_ref)`，重复收口更新正文，不新建。不把热重载中断排除出台账：规格要求中断登记，排除会让崩溃漏单。

**D8 轮询终态补上 `interrupted`。** `useTaskList` 的终态集合与 `task-detail.ts` 对齐，加入 `interrupted`。不新增筛选项，不改状态色。

## 模块防火墙自检

- 写库仍只在 `task_list/api.py`。`task_runner.py` 与 `apps.py` 不直接 `save()` 终态。
- `bug_manager` 继续只读 `Task`，由 `task_list` 在条件更新成功后调用 `record_task_bugs`。
- `run.py` 只打本机 drain 接口拿编号，不 import `apps.*`。
- 前端只读列表里的 `result` 摘要，不写库。
- 不新增跨 App 内部 import，不新增自定义异常类。

## Risks / Trade-offs

- [心跳 15 秒、阈值 45 秒，崩溃后最多约 45 秒才显示已中断] → 可接受。比「下次人工重启才收尸」短，且不会收走仍在跑的任务。
- [旧行 `heartbeat_at` 为空，服务一启动就被收成中断] → 这是想要的：没有心跳就不能证明线程还在。
- [两个服务进程短暂重叠时，旧进程心跳仍在，新进程不收] → 这是 D5 要守住的。旧进程死后，下一轮清扫收走。
- [停机名单文件写失败] → 降级为 `process_lost`，状态不错，只是原因粗。
- [条件更新与费用补写分成两次 SQL] → 费用补写失败只记日志，不回滚已经生效的终态。
- [助手对话仍把异常记成中断] → 本变更明确不做。任务清单和对话页的词暂时不一致，另立变更再对齐。
