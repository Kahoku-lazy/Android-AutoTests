# 关闭任务即断流：取消不再被 SOP 引擎吞掉，取消后也不提前放行设备

## Why

2026-11-06 09:47:20 用户在平台上关闭任务 `197`（结构化步骤-串口-全功能测试-02），数据库当场写成 `cancelled`，但执行线程又继续跑了 **230 秒**：期间 77 次设备操作（点击 / 拖拽 / 截图 / 查日志）、82 次模型调用、花费 ¥0.9394。实际停下靠的是 09:51:08 一次无关的工具异常打断了事件流，不是取消生效。

两个独立缺口叠加导致这个结果：其一，`asyncio.CancelledError` 在角色层被吞掉（AgentScope 的 `interruption_raise_cancelled_error` 默认为 `False`），SOP 引擎把这次中断理解成「本步失败」并自动重试，于是取消变成了继续跑；其二，取消信号只在「每条用例开头」检查一次，单用例任务永远命中不到这个检查点。同时 `cancel_running_task` 在发信号的同一刻就把任务置终态并放行设备槽，同一台手机的排队任务会被立刻拉起 —— 旧线程还在点屏幕，两条任务抢一台设备。

## What Changes

- 取消语义改为**事件边界立即断流**：工作流在每个事件上检查停止信号，命中即以取消异常结束当前步骤；当前步作废（不产生判决、不写运行汇总），已完成与已失败的用例清单原样保留。最坏延迟等于一次工具调用的阻塞时长（实测 0.3–5 秒）。
- 角色侧 ReAct 配置打开「中断后继续抛出取消」，使 `task.cancel()` 能穿透角色层，而不是被解释成一次可重试的失败尝试。
- 平台侧**取消不再放行设备槽**：`cancel` 只写终态，设备放行统一在工作线程退出时执行；另设超时兜底，工作线程超过时限未退出时强制放行并留一条事件，避免线程挂死把设备永久占住。
- 工作线程收尾 MUST NOT 覆盖已经写入的取消终态（取消与正常结束同时发生时，取消优先）。
- **非目标**：不新增 `cancelling` 中间态（不加“停止中”状态，不动前端状态映射）；不处理日志类工具异常打断整条用例的问题（另立变更）；不做断点续跑。

## 关联文档

- 无独立 PRD 编号：本变更收紧的是「关闭任务」的行为契约，依据为既有规格 `case-execution-continuity`、`agent-sop-workflow`、`ai-task-device-dispatch`、`task-execution-lifecycle` 与本次真机事故复盘。
- 事故记录：`dev_docs/DEV_TEST/UI自动化 问题记录.md`（记录任务 197 关闭后继续运行的时间线与花费）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `case-execution-continuity`: 「取消立即停止且不追加失败条目」由「当次循环边界」收紧为「事件边界越早越好，当前步作废」，并补充单用例任务同样必须响应取消。
- `agent-sop-workflow`: 新增「运行中收到停止信号即中断当前步骤」，明确工作流在事件边界检查停止信号、当前步不落判决的收口方式。
- `ai-task-device-dispatch`: 「同设备串行异设备并行」补充取消路径：取消 MUST NOT 提前释放设备槽，放行只发生在工作线程退出或兜底超时之后。
- `task-execution-lifecycle`: 新增「取消终态不被工作线程覆盖」，明确取消与正常收尾同时发生时的终态优先级。
- `agent-task-flow-report`: 新增「用户关闭的任务在报告里标为主动关闭」，把用户关闭导致的中断与引擎驳回的「未完成」区分开。

## Impact

- **engines**：`agents/workflow/ui_auto_workflow.py`（事件边界停止检查）、`agents/workflow/platform_run.py`（取消登记与每步检查、放行时机）、`agents/config/role_types.py` 与 `agents/agent_builders.py`（ReAct 配置字段与透传）
- **backend**：`apps/task_list/api.py`（`cancel_running_task` 不再放行设备、`finalize_task` 放行开关、兜底放行）、`apps/task_list/task_runner.py`（工作线程退出统一放行、终态守卫）
- **前端**：不改。取消后状态仍是 `cancelled`，只是「已关闭」这句话变成真的。
- **测试**：新增取消断流与设备放行的单元测试；`tests/graybox/unit/test_case_run_continuity.py` 的取消用例需覆盖单用例任务；角色配置透传补一条断言。
- **兼容**：不改数据库结构、不改状态枚举、不改接口字段；历史任务的 `cancelled` 记录不变。
