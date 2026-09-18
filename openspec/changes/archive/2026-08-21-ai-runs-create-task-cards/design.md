## Context

- AI 执行路径（`start_run`→`_run_ui_for_ai`→`_execute_tests`）全程 `client_task_id=""`，TaskCard 流程（idle→queued→running→done）完全未接入；`_run_client_task`（进程内 run_id→client_task_id 映射）是执行器与任务卡衔接的既有通道（队列流程在 `views/execution.py` 登记）。
- `_persist_run_start` 已支持 idle 卡片（enqueue→dequeue）、`_finalize_run` 已支持卡片终态（sm.complete/fail + case_items + overall 计数）、`_abort_run_before_execute` 已支持 mark_terminal（enqueue→dequeue→fail）——集成所需的消费端全部就绪，只差 AI 路径生产端。
- `start_run` 已预建 PENDING TestRunRecord（上一 change），而 `sm.dequeue` 目前无条件 `create`——两者同 run_id 必然撞唯一约束，dequeue 需幂等化。动机见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- 每次 AI 执行产生一张任务卡（task_id=run_id），出现在执行引擎任务列表并走到 done 终态（completed/failed/stopped + outcome + case_items）。
- 队列流程（UI 建卡）行为零变化。
- AI 路径既有的 PENDING 可见性、失败落库、设备释放行为全部保留。

**Non-Goals:**

- 不把执行日志写入任务卡 logs 字段（WS 事件流不变，logs 填充后续再议）。
- 不新增端点、不改前端（任务列表 30s 轮询自动可见）。
- 不改 run_id 命名（RUN-* 继续沿用）。

## Decisions

**D1：任务卡 task_id 直接等于 run_id（一对一）。**
卡片与运行一一对应，前端列表可唯一关联；避免引入第二套 ID 规则。task_id 长度 50 ≥ run_id 长度 ✓。

**D2：dequeue 用 `get_or_create` + 复用分支升级，而非无条件 create。**
新建路径（队列）语义与现有一致（含 started_at=now）；复用路径（AI 预建 PENDING）只升级状态/快照等字段、保留原 started_at（投递时间即开始时间）。不动 `_validate` 与卡片字段更新逻辑。

**D3：卡片创建与 `_run_client_task` 登记都在 `start_run`（api 层），执行协程只消费。**
保持"写库收敛 api.py"；`_run_ui_for_ai` 仅读取映射并透传给既有 abort 通道，改动最小。

## 模块防火墙自检

- 写库收敛：卡片经本模块 `save_task_card`（api.py 内），记录经状态机（sm.dequeue/complete/fail）。✅
- 跨 App import：无新增。✅
- 状态机：所有卡片状态迁移走 sm（enqueue/dequeue/complete/fail），无绕过。✅
- 通道：无新增 WS/SSE；前端无改动。✅

## Risks / Trade-offs

- [AI 卡片在 30s 轮询间隔内状态短暂为 idle/queued] → 状态机在进程内快速推进，任务列表刷新即见真实终态；与 UI 建卡行为一致。
- [卡片 logs 为空，详情页日志区无内容] → outcome/case_items/通过率仍可见，logs 填充留作后续（WS 事件可顺手落卡）。
- [进程崩溃时 idle/running 卡片残留] → `recover_orphans` 已有 running 卡片回收（→interrupted），无新增风险。
