## 1. 条件收口

- [x] 1.1 `task_list/api.py` 增加 `claim_terminal`：`UPDATE` 仅当 `status='running'` 时写入终态与合并后的 `result`；影响 0 行时不改状态和结果，只允许补用量与费用。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_closeout.py -q` 覆盖取消后异常不覆盖、重复收口不覆盖。
- [x] 1.2 `run_task_async` 的成功、`RunCancelled`、其它异常都改走 `claim_terminal`，删掉异常路径里的整段 `执行异常` 覆盖。验证：同一文件断言关闭后抛错仍为 `cancelled`，且 `workflow_id` 还在。

## 2. 失败类别与中断原因

- [x] 2.1 在 `task_runner.py` 按设计 D3 分类：`provider` / `device` / `platform` 写 `failed`，`BudgetExceeded` 写 `interrupted` 且 `cause=budget`，`RunCancelled` 写 `cancelled`。步骤没通过写 `failure_kind=verdict`；步骤结论为空不得写成成功。验证：`tests/task/unit/test_task_closeout.py` 四类失败加预算中断全过。
- [x] 2.2 `task_result_preview` 优先读 `reason`，不把异常堆栈或网关长文下发。验证：同一测试文件断言 `provider` 摘要是短句，且列表筛选用的 `workflow_id` 仍可解析。

## 3. 心跳与清扫

- [x] 3.1 `Task` 增加可空 `heartbeat_at` 及迁移。工作线程用旁路 daemon 定时器每 15 秒只更新仍为 `running` 的行，`finally` 取消定时器。验证：`python manage.py makemigrations --check` 无残留，且单测能把心跳写成非空。
- [x] 3.2 用 45 秒阈值、30 秒间隔的清扫替换只跑一次的启动恢复。只收心跳超时或心跳为空的 `running`；心跳未超时不动。只在 ASGI 服务进程跑，跳过 autoreload 父进程、管理命令和测试。收尸后仍 `dispatch_device`。验证：`tests/task/unit/test_task_sweep.py` 覆盖「心跳还在不收」「心跳超时收成 `process_lost` 并拉起 pending」。

## 4. 停机超时名单

- [x] 4.1 `run.py` 在排空等满 180 秒、杀进程前，把当时仍为 `running` 的任务编号写入 `temps/stop-timeout-tasks.json`。后端不可达时不写文件，不因此阻止停止。验证：用假的 drain 响应跑一段提取函数，断言只写下编号和时间。
- [x] 4.2 清扫读到名单则对这些编号写 `cause=stop_timeout`，用过后删除文件；名单里没有的超时任务仍是 `process_lost`。验证：`tests/task/unit/test_task_sweep.py` 两条都过。

## 5. BUG 与清单

- [x] 5.1 `bug_manager/extract.py`：`provider` / `device` / `platform` 用来源键 `task:provider`、`task:device`、`task:platform` 各建一张；`verdict` 仍按用例拆；中断正文按 `cause` 写，不写「服务重启」。重复收口不新建。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket/unit/test_bug_ticket_extract.py -q`。
- [x] 5.2 `useTaskList` 的终态集合加入 `interrupted`，与 `task-detail.ts` 对齐。不新增状态标签。验证：`cd frontend && npx vitest run tests/task-list/p0/useTaskList.spec.ts`。

## 6. 门禁

- [x] 6.1 后端相关测试与边界：`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_closeout.py tests/task/unit/test_task_sweep.py tests/bug_ticket/unit/test_bug_ticket_extract.py -q`，以及 `python utils/gen_arch_stats.py --check-boundaries`。验证：两条命令退出码为 0。
- [x] 6.2 `openspec validate --change task-outcome-closeout`。验证：命令退出码为 0。
