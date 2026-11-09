## 1. 日志证据：返回中断结果而不是抛异常

- [x] 1.1 `engines/agents/tools/tool_serial.py`：`check_device_log` 在窗口为空、窗口未盖满时改为返回 `FAIL` + `reason`（原文用 `LOG_EMPTY` / `LOG_SPAN_SHORT`）+ `evidence_missing=true`，不再 `raise ValueError`；同步改函数 docstring 的 Raises 段；验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/test_log_check_evidence.py -q` 通过（无日志 → FAIL 且不抛；未盖满 → FAIL 且不抛；有日志无关键词 → FAIL）。
- [x] 1.2 `engines/agents/tools/tool_wrapper.py`：删除把 `LOG_EMPTY` / `LOG_SPAN_SHORT` 转成 `DeveloperOrientedException` 的分支与相关 import；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit -q -k "log or serial"` 无新增失败，且工具调用不再产生 `ExceptionGroup`。
- [x] 1.3 提示词：`CASE_VERIFIER_PROMPT` 之外的验收提示词（`engines/agents/config/data/prompts/` 下验收角色）补一句「工具结果带 `evidence_missing` 时不得判 FAIL，应如实说明证据不可用」；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_authoring_prompts.py tests/engines/agents -q` 通过且提示词断言同步更新。

## 2. 工作流：单步中断不打死整条用例

- [x] 2.1 `engines/agents/workflow/ui_auto_workflow.py`：新增中断收集器与 `_ResilientSOPStep(SOPStep)`，包装 `reply_stream`：捕获异常 / 识别 `evidence_missing` → 记（步骤序号、标题、类型、原因、工具名）→ 置该步 `phase = COMPLETED` → 正常返回让引擎推进；验证：新增单测 `tests/graybox/unit/test_step_interrupt_continue.py` 覆盖「第 2 步异常 → 第 3、4 步照跑」和「最后一步异常 → 用例未完成」。
- [x] 2.2 同文件：`run_workflow` 在收集器非空时返回 `interrupted` 相位；`_drive_real` 把该用例记入 `failed`（中断步也记为 `FAIL`，计入通过/失败统计），`reason` 点名步骤标题与中断类别；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_platform_cancel.py tests/graybox/unit/test_case_run_continuity.py -q` 全绿，且新增用例断言 `failed` 含该用例标题、`reason` 里出现步骤标题与「证据不可用 / 异常中断」之一。
- [x] 2.3 同文件：`_emit_interrupt` 改为 `await show_event(record, buf, models, flush=True)`；验证：单测里用一个记录调用的替身 `show_event` 断言它是被 await 的（不是直接 `sink.emit`）。

## 3. 事件落库：失败不丢行

- [x] 3.1 `backend/apps/task_list/event_store.py`：`flush()` 改为成功才清空缓冲，失败把行放回并按 `(task_id, seq)` 去重；新增 `_RETRY_MAX_ROWS = 500` 上限与超限告警；`close()` 再试一次后仍失败才丢弃并告警；验证：新增 `tests/api/test_task_event_retry.py` 覆盖「首次写失败 → 下次写入补齐、序号连续」与「超上限丢最旧并告警」。
- [x] 3.2 同文件：`emit()` 在检测到当前处于事件循环（`asyncio.get_running_loop()` 可取）且直接调用时，MUST 抛一条可识别的错误或转交线程，不允许静默丢行；验证：单测构造 async 上下文调用并断言不再静默丢弃（走转交或明确报错）。
- [x] 3.3 回归：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_store.py tests/api/test_task_event_flow.py tests/api/test_task_cancel_dispatch.py -q`；验证：全绿，`ai_usage_hourly` 与费用口径不变。

## 4. 报告与界面：中断类型与原因

- [x] 4.1 `backend/apps/task_list/task_reports.py`：`_interrupt_maps` 读出 `interrupt_kind`（`log` 证据不可用 / `exception` 执行层异常）与 `interrupt_tool`，步骤对象新增这两个可选字段；被中断的步骤 `outcome` MUST 为 `FAIL`（不是「未完成」）；验证：新增 `tests/api/test_task_report_interrupt.py` 用例断言两类中断都落 `FAIL`、类型与工具名正确，原有 `interrupt` 原文保持。
- [x] 4.2 `frontend/src/modules/task-list/components/CaseStepList.vue` + `helpers/report-steps.ts`：中断步骤显示 `FAIL` 徽标 + 按 `interrupt_kind` 渲染「日志中断」/「异常中断」，`title` 为原因全文；验证：`cd frontend && npm run typecheck` 与 `npx vitest run tests/task-list` 通过。
- [ ] 4.3 界面上真实任务可见（任务 201 的中断事件已随整批丢失，只能对新运行验证）：新跑一条 ≥2 步任务并在中途制造日志空洞，详情页被中断步骤显示 `FAIL` +「日志中断 / 异常中断」，悬停能读到原因原文；验证：目视确认后记录到 `dev_docs/DEV_TEST/UI自动化 问题记录.md` §7.5。

## 5. 门禁与回归

- [x] 5.1 engines 自检：`python -m scripts.docstrings check` 与 `python -m scripts.check_engines_agents_style`（在各自技能目录下）；验证：本次新增/修改行 0 告警，存量 23 条不变。
- [x] 5.2 全量相关回归：`python -m pytest -c tests/pytest.ini tests/graybox/unit tests/api/test_task_*.py -q`；验证：无新增失败（既有失败逐条说明来源）。
- [x] 5.3 本地门禁：`python run.py check`；验证：阻塞项通过（`vitest` 若因未提交的前端改动失败，需说明不是本次引入）。
- [ ] 5.4 真机验证：跑一条 ≥2 步且带日志断言的用例，人为制造日志空洞（或选中日志断流时段），确认该步显示「异常中断/日志中断」、后续步骤继续执行、任务结果原因含该步标题；验证：任务详情页与 `task_tasks.result` 一致，且该任务事件序号连续无缺口。

## 6. 任务 204 复盘出的两处回归

- [x] 6.1 **中断事件没落库**：`_emit_interrupt` 原来走 `show_event` → `fold.step` 按 AgentScope 事件类型名分派，`EventRecord` 一个都不匹配，被静默丢成空结果（任务 201/204 因此一条 `StepInterruptedEvent` 都没有）。改为新增 `AgentEventsShow.emit(record, flush=)` 直写接收方，并经 `database_sync_to_async(..., thread_sensitive=False)` 转线程（`asgiref` 会复制 ContextVar，接收方仍可见）。验证：单测绑一个替身 sink，断言 `run_workflow` 结束后 sink 收到 `StepInterruptedEvent`；不再用「替身 `show_event` 收到事件」这种测不到落库的断言。**验证结果**：通过 —— 实现落在既有的 `event_sink.emit_record`（`model_retry.py` 已是同一用法）；`tests/graybox/unit/test_step_interrupt_continue.py::test_interrupt_event_reaches_sink` 断言替身 sink 收到一条 `StepInterruptedEvent`；`tests/api/test_task_event_store.py::test_interrupt_event_from_running_loop_writes` 断言该记录真的写进 `task_events`（`step_seq`/`attempt`/`case_title`/`payload.kind` 全对）。
- [x] 6.2 **失败原因漏报被驳回的步骤**：`run_workflow` 只要收集器非空就按 `interrupted` 收口，`reason` 只拼中断原因；任务 204 第 8 步「验收驳回 2 次」因此完全没出现在原因里。`AgentSOPWorkflow` 新增 `failed_steps`（验收驳回到上限、且不是中断的步骤：序号 / 标题 / 驳回次数 / 最后一条驳回说明），`platform_run._failure_detail` 同时汇总两类。验证：单测断言原因里同时出现第 7 步中断与第 8 步驳回。**验证结果**：通过 —— `test_rejected_step_is_collected_as_failure`（第 2 步驳回 2 次、原因含驳回说明、标题取动作原文）、`test_failure_detail_covers_interrupt_and_rejection`（同时出现「第 7 步 … 证据不可用」与「第 8 步 … 验收驳回 2 次」）、`test_interrupted_step_is_not_reported_as_rejection`（同一处不重复报）、`test_failure_detail_counts_overflow`（超三条给总数）。


