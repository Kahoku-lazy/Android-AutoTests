## Context

动机见 `proposal.md` - Why。落地约束（均已按代码核对）：

- `engines/agents/tools/tool_serial.py:353-356`：日志窗口为空 / 没盖满 5 秒时 `raise ValueError(LOG_EMPTY | LOG_SPAN_SHORT)`。
- `engines/agents/tools/tool_wrapper.py:127-129`：捕获这两个 `ValueError` 后转成 `DeveloperOrientedException` 继续抛，因此它不是「工具结果」而是「回调异常」。
- AgentScope 并发工具把同批异常聚合成 `ExceptionGroup("One or more tool calls raised an exception", ...)`（`agentscope/agent/_agent.py:2313`）抛回工作流。
- `engines/agents/workflow/ui_auto_workflow.py:226-231`：`except Exception` 只记 `StepInterruptedEvent` + 打日志，随后 `dump()`、返回 `engine.phase`（停在 `running`），**整条用例到此结束**。
- `engines/agents/workflow/ui_auto_workflow.py:_emit_interrupt` 直接 `current_sink().emit(record)`，即它是**在事件循环线程里同步写库**；普通事件走 `show_event` → `database_sync_to_async`。
- `backend/apps/task_list/event_store.py`：`_BATCH = 50`；`flush()` 先把 `self._rows` 取出清空再插入，插入抛错时按行重试，失败行只记 warning 后丢弃——所以一次上下文错误会整批丢 50 行。
- `backend/apps/task_list/task_reports.py:_interrupt_maps` 从 `StepInterruptedEvent.payload.reason` 取原因，写入步骤的 `interrupt` 字段；前端 `CaseStepList.vue` 在 `interrupt` 非空时渲染固定文案「日志中断」。

## Goals / Non-Goals

**Goals:**

- 日志证据拿不到时只让**这一步**中断，后面的步骤照跑；被中断的步骤记为 `FAIL` 并计入失败统计。
- 中断一定留下类别与原因（执行层异常 / 证据不可用），并在详情页可见，定位问题不需要翻后台日志。
- 事件写入不再因调用上下文（事件循环线程）或一次抖动而整批丢失。

**Non-Goals:**

- 不修设备日志断流本身（采集链路问题，另案）。
- 不改 5 秒窗口、起点解析、关键词表与「起点之前不看」的口径。
- 不把「证据不可用」表述成设备或应用执行出错（仍记 `FAIL`，但原因必须讲清是证据问题）。
- 不改事件表结构与接口字段名（只在 `interrupt` 旁新增可选字段）。

## Decisions

### D1. 日志工具改为返回「证据不可用」结果，不再抛异常

`check_device_log` 在窗口为空 / 未盖满时返回 `FAIL` + `reason` + `evidence_missing=true`；`tool_wrapper` 删除把 `LOG_EMPTY` / `LOG_SPAN_SHORT` 转成 `DeveloperOrientedException` 的分支。

- 为什么不再抛：抛异常等于「工具坏了」，会被 AgentScope 聚合成组异常、穿透整个执行流；而「日志没抓到」是**证据状态**，应该像其它业务结论一样以结果形式回到模型与工作流手里。
- 备选（保留抛错、只在工作流里兜住）：模型看不到原因，无法改换证据方式；且异常穿透路径随库版本变化，脆。
- 备选（直接返回 `FAIL` 不带标记）：工作流无法区分「设备没响应」与「日志没抓到」，会把证据缺失计成失败，正是本次要避免的误判。

### D2. 单步中断由工作流侧的子类步骤承载，不进 AgentScope 引擎

新增工作流内部的 `_ResilientSOPStep(SOPStep)`：包装 `executor/verifier` 的 `reply_stream`，捕获异常并把中断记进共享收集器，然后**把该步 `state.phase` 置为 `COMPLETED` 并正常返回**，让 `SOPEngine` 继续推进到下一步；`run_workflow` 结束时若收集器非空，返回 `interrupted` 相位（而不是引擎给的 `running`/`failed`），由 `_drive_real` 把该用例记为失败。

- 为什么置 `COMPLETED`：引擎只认自己的相位来决定是否继续下一步，没有「跳过」语义；用 `COMPLETED` 是唯一不入侵引擎的做法。该步的**结论**由收集器决定并写成 `FAIL`，不依赖 `engine.phase`。
- 备选（改 AgentScope）：外部依赖，不可控也不可测。
- 备选（自研步骤循环替换引擎）：等于重写执行编排，改动面远超本变更。
- 收集器同时保存：步骤序号、标题、类别（`log` 证据不可用 / `exception` 执行层异常）、原因、工具名，供任务结果与报告使用。
- 中断步在 `engine.state` 里记一条驳回（`record(False, 原因)`），保证运行汇总与报告口径一致：中断即该步未通过（`FAIL`），并计入失败统计。

### D3. 中断事件走异步安全通道

`_emit_interrupt` 改为 `await show_event(record, buf, models, flush=True)`（工作流本来就是 async），复用 `database_sync_to_async`；不再直接 `current_sink().emit(...)`。

- 备选（在 sink 内部判断线程再转交）：sink 是同步 API，运行在事件循环里时无法 `async_to_sync` 回主线程，只能抛错或阻塞，不如在调用点改 async。

### D4. 写入失败保留待写行

`TaskEventSink.flush()` 改为「成功才清空」：失败时把行放回缓冲头部继续重试；缓冲设上限（`_RETRY_MAX_ROWS`，默认 500），超过上限丢最旧的行并写一条告警，避免一次长故障吃光内存。收尾 `close()` 再试一次，仍失败才丢弃并告警。

- 为什么不是「失败就退回逐行、逐行失败就算了」：现状正是这条路径一次性丢掉 50 行；保留重试能把「上下文错误」「瞬时断连」都救回来。
- 风险：重复写入。行本身带 `seq`，若批量实际成功而回包超时，重试会撞主键——重试前按 `(task_id, seq)` 去重，或依赖主键冲突按行跳过（冲突视为已写入）。

### D5. 报告新增中断类型字段，前端按类型渲染

步骤对象在保留 `interrupt`（原因原文，兼容）之外新增 `interrupt_kind`（`log` / `exception`）与 `interrupt_tool`（可选）。前端把现有固定文案「日志中断」改为按 `interrupt_kind` 渲染「日志中断」或「异常中断」，`title` 仍是原因全文。

- 备选（前端按原因文本猜类型）：字符串匹配脆，且以后加类型还要改前端。

## 模块防火墙自检

- 跨 App import：无新增。改动集中在 `engines/agents/**`、`backend/apps/task_list/**`、`frontend/src/modules/task-list/**`。
- 写库路径：事件写入仍只经 `task_list/api.py` 的 `insert_task_events`；`event_store` 与 `task_reports` 同属一个 App。
- engines 边界：日志工具只改返回结构，不引入 `apps.*` / `django.*`；中断收集器留在 `workflow/`，不创建角色、不绑定工具。
- 前端：只改步骤行渲染与类型，不新增接口调用。

## Risks / Trade-offs

- [把中断步置 `COMPLETED` 可能让引擎误以为该步通过，进而 `handover` 传空给下一步] → 中断时同时记一条驳回并向下交付一条显式说明（「本步中断，原因…」），下一步能看到上下文而不是空白。
- [证据不可用也记 `FAIL`，会让通过率反映环境问题] → 中断类别与原因随步骤下发，报告与任务结果都能区分「执行层异常」与「证据不可用」；后续若要做「剔除环境导致的失败」统计，分类字段已经就位。
- [中断后继续跑后续步骤可能放大成本] → 只有中断步跳过重试；用例级别的预算上限（模型调用数 / 时长）仍然生效。
- [保留待写行重试会放大内存] → `_RETRY_MAX_ROWS` 上限 + 超限告警 + 收尾强制清空。
- [日志工具返回 `FAIL` 后，验收模型可能直接把该步判失败] → `evidence_missing` 会随工具结果给出，工作流优先按「中断」处理，且提示词明确「证据不可用不要判失败」。
- [重复写入撞主键] → 重试前按 `(task_id, seq)` 去重，冲突按已写入处理。

## 迁移与回滚

- 无数据库迁移；新增的报告字段为可选，旧任务读不到时按「无中断」渲染。
- 回滚：单独回滚本次提交即可；日志工具恢复抛错路径、sink 恢复「失败即丢」、报告字段不再下发（前端已做缺省处理）。
