## Context

现状见 `proposal.md - Why`。方案只需要回答三件事：报告在哪一层补齐、中断信息怎么进报告、报告定位怎么回到任务。相关约束：

- `engines/backend_bridge/workflow/bound_sop.py` 在 `run_sop` 返回后才调用 `capture.finish()` 渲染报告；`run_sop` 内部没有 `try/finally`，异常会直接穿过 `recorder.finish()`。
- 事件日志在 `AgentEventRecorder.begin()` 时就已打开并逐条 flush，中断时磁盘上已有可渲染的素材。
- `engines/ae_harness` 不被本次改动触碰：`backend-bridge-sop` 与 `agent-sop-runner` 的既有条款要求本层不改 `ae_harness`。
- `task_runner` 的失败分支只写原因与失败步骤，正常分支才带 `_report_locator`。

## Goals / Non-Goals

**Goals:**

- 已开始执行的 SOP 运行，在非取消、非预算超限的异常中断后仍落一份 HTML 报告，且报告明确标注「运行中断」。
- 报告定位经失败回调回到 `task_runner`，写进失败 payload 的 `report_run` / `report_name`。
- 任务清单按钮与报告台账按既有字段自动生效，不改前端与台账代码。

**Non-Goals:**

- 不改 `engines/ae_harness`（不加 `run_sop` 钩子、不改报告渲染器）。
- 不为取消（`cancelled`）、预算中断与重启中断（`interrupted`）产出报告。
- 不为起跑前失败（设备校验、工作流编号缺失、角色装配、`run_sop` 在 `on_begin` 之前失败）伪造报告。
- 不回填历史失败任务；不做红色横幅、失败详情页、报告保留策略。

## Decisions

### 决策 1：在 `bound_sop` 收尾，不动 `run_sop`

`_SopCapture.start(recorder)` 已能从 `on_begin` 拿到 recorder。给它补两个字段（recorder 与起始时刻）和一个 `abort(exc) -> Path | None`：补写 `recorder.finish(cost_s)` 的收尾汇总、`raw.end()/close()`、`aligned.set_steps([])`、`aligned.end({... aborted ...})`，最后用既有的 `AlignedReportRenderer` 渲染 HTML，返回 `record.html_path`。

`run_bound_sop` 把 `await run_sop(...)` 包进 `try/except`：`RunCancelled` 与 `BudgetExceeded` 原样抛出（不渲染）；其余异常先 `capture.abort(exc)`，再调用失败回调，最后 `raise` 原异常。

理由：`run_sop` 的返回值语义（`SopResult`）不需要改变，取消/预算的异常语义也不变；改动集中在一个文件。
备选：在 `run_sop` 里加 `on_abort` 钩子（更通用），但要改 `ae_harness`，与既有规格条款冲突，本次不选。

### 决策 2：失败定位用回调，不新增异常类型

`run_bound_sop(..., on_abort: Callable[[Path | None, Exception], None] | None = None)`。`task_runner` 在 `run_task_async` 里放一个可变 dict，`_run_assistant_sop` 把 `on_abort` 闭包写成 `holder["report_path"] = path`，异常分支读它并传给 `_failure_payload`。

理由：`engines` 红线禁止随意新增自定义异常类；回调比"给异常对象打属性"更显式。
备选：`raise RunAborted(report_path=...) from exc`（需新增异常类，否决）；失败后扫最新目录（脆弱，否决）。

### 决策 3：中断信息写进 `run` 元数据，不新增渲染分支

`aligned.set_steps([])` 后报告没有「步骤结论」卡。中断信息分两处落：

- `aligned.end({"aborted": True, "abort_reason": reason, ...})` 把中断标记与原因写进 `aligned.json`，供程序和后续排查读取；
- 渲染 HTML 前把 `aligned.document["run"]["运行中断"] = reason` 注入文档。渲染器会把 `run` 的所有键值对渲染到概览，因此无需改 `render_aligned.py` 就能让报告显示「运行中断：<原因>」。

取舍：`aligned.json` 的 `run` 段不含这个中文键（`run` 在 `begin` 时复制），以 `summary.aborted` / `summary.abort_reason` 为准；HTML 概览里是一行键值而不是红色横幅，醒目度弱一些。换来 `ae_harness` 零改动。

报告同时不写「每一步都通过了」类文案（没有 steps 卡，天然不出现）。

### 决策 4：失败 payload 复用既有定位字段

`_failure_payload(exc, failed_steps=None, report_path=None)` 追加 `**_report_locator(report_path)`（已有函数，空路径返回 `{}`）。`_report_locator` 已经按 `REPORT_ROOT` 拆出 `report_run` / `report_name`，与成功路径同一口径。

失败收尾自身再出错时，`abort()` 内部捕获并写一条 `agent_event_log` 警告，MUST NOT 用收尾异常覆盖原异常。

### 决策 5：不改前端与台账

任务行与台账都已按 `report_run` / `report_name` 工作：`serialize_agent_task_row` 直接从 `Task.result` 派生，`report_inventory._sop_item` 只过滤是否有定位。定位一旦写进 payload，按钮与台账自动出现。

## 模块防火墙自检

- 跨 App import：无新增。`task_runner`（backend）只 import `engines.backend_bridge`（既有方向）；`bound_sop` 只 import `engines.*` 与 stdlib。
- 跨 App 写库：无。任务终态仍只经 `backend.apps.task_list.api.claim_terminal`。
- DB：无新表、无新字段、无迁移。
- 前端：不直连、不改代码。
- 新依赖：无。

## Risks / Trade-offs

- **[报告被误读为正常跑完]** → 概览固定写「运行中断：原因」，且不生成步骤结论卡；报告不写「每一步都通过了」。
- **[失败收尾掩盖原异常]** → `abort()` 全包兜底，原异常始终重新抛出；收尾失败只记 `agent_event_log`。
- **[孤儿报告]** → 报告已落盘但 `claim_terminal` 失败或被取消抢先时，任务不带定位，台账不显示；文件留盘，接受。
- **[预算中断口径冲突]** → `sop-task-run` 写的是「预算超限任务状态为失败」，而 `task_runner` 把 `BudgetExceeded` 映射为 `interrupted`。本次按现状跳过预算中断，不在本变更裁决该冲突；若后续把预算改成 `failed`，需要同步放开 `bound_sop` 的跳过名单。
- **[磁盘增长]** → 每次失败多一份 HTML；事件日志本来就会落盘，HTML 增量很小。暂不做保留策略。
- **[`run_sop` 在 `on_begin` 之前失败]** → 没有 recorder 引用，无法渲染；这类失败仍只写原因（已知边界）。

## Migration Plan

- 无数据库迁移、无接口破坏、无配置项。
- 发布后只对**新发生**的失败生效；历史失败任务没有事件记录可补，不回填。
- 回退：还原 `bound_sop.py` 与 `task_runner.py` 两个文件；已生成的失败报告是普通 HTML，留在报告目录不影响运行，可按需删除。

## Open Questions

- 是否把「运行中断」升级为报告顶部的红色横幅：需要解除 `ae_harness` 零改动条款，另开变更。
- 起跑前失败的失败原因在任务清单可见（B 方案）：本次不做，另开变更。
