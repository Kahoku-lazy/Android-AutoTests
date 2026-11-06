## Context

动机见 `proposal.md` - Why。落地位置与现状约束（均已按代码核对）：

- `engines/agents/workflow/platform_run.py`：`run_platform_sop` 用 `asyncio.run(_drive_real(...))` 跑整轮；`bind_cancel(task_id)` 注册 `threading.Event`，`request_cancel(task_id)` 置位事件并把 `task.cancel()` 投递到 `_inflight` 里登记的 asyncio 任务。`_drive_real` 只在 `for case in cases` 的顶部检查事件（`platform_run.py:207`），单用例任务永不命中；取消真正生效只能依赖 `task.cancel()` 抛到 `_drive_real` 的 `except asyncio.CancelledError`（`:236`）。`_cancelled()` 产出 `status=cancelled` 并把已完成/未完成清单原样带回。
- `engines/agents/workflow/ui_auto_workflow.py`：`run_workflow` 用 `async for event in engine.reply_stream(...)` 消费事件，`except Exception`（`:226`）只接异常、接不住 `CancelledError`（`BaseException` 子类）。
- AgentScope 2.0.9：`ReActConfig.interruption_raise_cancelled_error` 默认 `False`，`agent/_agent.py:1271-1281` 在 `except asyncio.CancelledError` 里只在标志为真时 `raise`，否则吞掉并正常返回；并发工具路径还会 `asyncio.current_task().uncancel()`（`_agent.py:2306`）。因此 `task.cancel()` 在本项目里等价于「打断当前一次回复」，SOP 引擎把它当成一次失败尝试并自动重试。
- `engines/agents/config/role_types.py` 的 `ReActConfig` 只有 `max_iters` / `structured_output_grace_iters` / `stop_on_reject`；`agent_builders._as_react_config`（`:81`）映射这三项到 `agentscope.ReActConfig`。
- `backend/apps/task_list/api.py`：`cancel_running_task`（`:394`）发信号后立刻 `finalize_task(status=CANCELLED)`；`finalize_task`（`:345`）末尾无条件 `dispatch_device(task.device_serial)`（`:369-371`），即取消当场释放设备槽。
- `backend/apps/task_list/task_runner.py`：`run_task_async` 的 SOP 分支（`:59-80`）不校验任务当前状态就直接 `finalize_task`；只有用例编写分支（`:50`）做了 `status != CANCELLED` 守卫。

## Goals / Non-Goals

**Goals:**

- 关闭任务后，正在跑的那一步在**下一个事件边界**停止，最坏不超过一次工具调用的阻塞时长。
- 取消不再被角色层解释为「一次失败尝试」，因此不触发重试、不推进后续步骤。
- 取消期间设备槽保持被占用，同设备排队任务不会在旧线程还在点屏幕时被拉起。
- 「已关闭」成为可信终态：工作线程收尾不得把它改写成别的状态。

**Non-Goals:**

- 不新增 `cancelling` 中间态，不改任务状态枚举、序列化与任务卡的状态徽标（报告里新增的「主动关闭」属于步骤/用例结果口径，不是任务状态）。
- 不处理日志类工具异常（`check_device_log` 的 `ExceptionGroup`）打断整条用例的问题 —— 改的是执行/验收的失败判定路径，另立变更。
- 不做断点续跑：被中断的用例重跑仍从第 1 步开始。
- 不清理事件流里已产生的过程物（截图、工具调用、费用），它们照常保留与计费。

## Decisions

### D1. 停止信号以「回调 + 事件边界检查」为主，`task.cancel()` 作为加速手段

`AgentSOPWorkflow.run_workflow` 增加可选入参 `should_stop: Callable[[], bool] | None`，在 `async for event in engine.reply_stream(...)` 的**每次循环体**里检查；为真即 `raise asyncio.CancelledError`。`platform_run._drive_real` 保存 `cancel_event`，构造工作流时传入 `cancel_event.is_set`，并保留原有的 `task.cancel()` 投递。

- 为什么不用自定义异常：`engines/` 红线禁止随意新增异常类，且 `_drive_real` 已经用 `except asyncio.CancelledError` 收口到 `_cancelled()`，语义正好。
- 为什么不用「返回 cancelled 阶段」：`engine.reply_stream` 是生成器，提前 return 会让 `engine.state` 停在该步的 `running`，但引擎循环仍可能被外部再次驱动；抛取消能让整条调用栈一次性退出，不留半开的生成器。
- 备选（只靠 `task.cancel()`）：已被事故证伪 —— 库默认吞取消。
- 备选（只靠回调）：卡在一次长模型调用时要等这次调用返回，实测 1–6 秒，仍满足「5 秒内生效」的典型场景，但遇到慢调用会接近上限；因此两点并用。

### D2. 打开角色的 `interruption_raise_cancelled_error`

角色侧 `ReActConfig` 增加 `interruption_raise_cancelled_error: bool = True` 字段，`_as_react_config` 透传到 `agentscope.ReActConfig`。这样 `task.cancel()` 在模型调用/工具调用中途也能直接向上抛，不必等下一个事件。

- 本项目不使用 `UserInterruptEvent`（人工打断）语义，打开该标志不影响现有交互路径。
- 备选（在库外包一层拦截器）：需要依赖 AgentScope 内部事件顺序，比一个官方开关更脆。

### D3. 取消不再放行设备槽，放行统一在工作线程退出时发生

`finalize_task` 增加关键字参数 `release_device: bool = True`；`cancel_running_task` 传 `release_device=False`，只写终态。设备放行统一由 `run_task_async` 的 `finally` 调用一次。

- 兜底：`spawn_task_thread` 把工作线程登记进模块级表；`cancel_running_task` 在写终态后调度一个 60 秒的 daemon `threading.Timer`。超时若线程仍存活，写一条告警事件（走事件接收方，进任务时间线可见）并强制放行；线程正常退出时取消该 Timer。
- 为什么用 Timer 而不是 `cancelling` 状态：前者只加一个后台计时器，不动状态机；后者要连带改枚举、前端、报告与所有「非终态=运行中」的判断，为秒级窗口不值。
- 重复放行是安全的：`dispatch_device` 本身先查该 serial 是否已有 `running`，重复调用不会拉起第二条。

### D4. 工作线程收尾尊重已有终态

`run_task_async` 的 SOP 分支在 `finalize_task` 前 `refresh_from_db()`；若当前状态已是 `cancelled`，则只回写用量与费用（`usage`），不改 `status` / `result` / `finished_at`。与用例编写分支（`:50`）保持同一口径。

### D5. 事件边界检查的粒度就是「一次事件」

每个事件包含模型增量、工具调用、工具结果等，实测间隔 0.01–6 秒。检查成本是一次字典查找 + 一个 `Event.is_set()`，不引入可测量的开销。

### D6. 取消在报告里单独标「主动关闭」，复用现有中性徽标

后端 `_step_outcome` / `_case_outcome` 增加 `cancelled` 入参（来自 `task.status == "cancelled"`）：已开始未判决 → `主动关闭`，未开始 → `未执行`，已有判决保持 `PASS`/`FAIL`。前端只做两处映射：步骤徽标走既有的 `is-idle`（灰），用例徽标走既有的 `badge-pending`（中性灰）。

- 为什么不复用「未完成」：`未完成` 在本项目里表示「引擎驳回达到上限或事件流被打断」，与「用户主动关掉」是两种原因，混用会让复盘时无法区分「跑挂了」与「我关的」。
- 为什么让后端出值而不是前端改写：报告接口是结果口径的唯一真相源，导出/统计/第三方读取都走它；只在前端改文本会让接口继续撒谎。
- 备选（前端按 `task.status` 覆盖文本）：改动更小，但接口与页面两份口径，后续接入方要各自实现一遍。
- 备选（新增独立字段 `interrupted_by`）：语义更干净，但要动接口契约与前端类型；本次先复用 `outcome`，不扩字段。

## 模块防火墙自检

- 跨 App import：无新增。改动集中在 `engines/agents/**` 与 `backend/apps/task_list/**`。
- 写库路径：任务状态与用量写入仍只经 `task_list/api.py` 的 `finalize_task` / `dispatch_device`；`task_runner` 与 `api` 同属一个 App，未跨 App 调用内部实现。
- engines 边界：`platform_run` 只多了一个 `Callable[[], bool]` 形参，未反向依赖 `apps.*` / `django.*`；`ui_auto_workflow` 不感知线程与数据库。
- 前端：不涉及，无直连数据库、无仪表盘写操作。

## Risks / Trade-offs

- [阻塞中的工具调用无法被打断] → 最坏延迟 = 一次 adb/OCR/日志查询的阻塞时长（实测 0.3–5 秒）；规格已把上界写成「一次工具调用内」，不承诺硬实时。
- [打开 `interruption_raise_cancelled_error` 会改变角色层对取消的处理] → 本项目没有依赖「吞掉取消后继续」的路径（无 `UserInterruptEvent` 用法）；回归用例覆盖「未提供停止信号时行为不变」。
- [在未调用 `cancel()` 的任务里主动抛 `CancelledError`] → Python 允许；`_drive_real` 已捕获并转成 `_cancelled()`，`asyncio.run` 不会把它当成未处理取消。回归用例覆盖该路径。
- [兜底 Timer 与工作线程退出重复放行] → `dispatch_device` 内已有「同 serial 已有 running 则跳过」判定，重复调用幂等。
- [取消瞬间恰好在写终态，与工作线程收尾竞争] → D4 的守卫让 `cancelled` 优先；对同一行只做字段级更新，不整行覆盖。

## 迁移与回滚

- 无数据库迁移、无接口字段变化、无配置项格式变化（`agent_config.yaml` 不新增必填项，`ReActConfig` 新字段有默认值）。
- 回滚：单独回滚本次提交即可；`cancelled` 历史记录不受影响，设备槽放行回到 `finalize_task` 内联执行。
