## Context

- AI 执行链路：`run_test` 工具 → `test_runner.api.start_run`（同步校验+投递，立即返回成功）→ Daphne 主循环 `_run_ui_for_ai`（权威锁 → 预检连接 → `_execute_tests`）→ `_execute_tests._persist_run_start` 才创建 `TestRunRecord`。
- 现状缺陷：`start_run` 与 `_persist_run_start` 之间的所有失败（锁失败 ValueError 分支、连接失败 abort 分支）不落任何记录；`get_run_status` 只能报"run 不存在"；WS 事件（`on_log`/`on_device_error`）在 AI 对话场景无订阅者，信息完全蒸发。
- `device_pool.api.acquire_device` 的 BUSY 分支对"同一用户重入"本应放行（注释"AI 可能已 acquire"），但 `occupied_by`(CharField) 与 `user_id`(int) 类型不匹配使放行条件恒假。
- `TestRunStatus` 为小写五值枚举（pending/running/completed/stopped/failed）；`TestRunRecord.run_id` 唯一；动机与完整证据链见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- 每次 `run_test` 都有可查询的 `TestRunRecord`：投递即 PENDING，执行升级 running，任何执行前失败终态为 failed/stopped 并携带错误摘要。
- AI 自锁设备后执行不再被误判"他人占用"。
- AI 从 `get_run_status` 即可获得具体失败原因，无需猜测重试。

**Non-Goals:**

- 不改 `TaskCard` 任务流的状态机（`sm.dequeue/fail/complete` 路径不动）。
- 不新增端点、不改前端；不改 `run_test` 返回形状。
- 不做同设备并发执行的互斥改造（AI 重复 run_test 的并发防护不在本 change 范围）。

## Decisions

**D1：预建记录放在 `start_run`（api.py 内联），而不是执行协程里。**
同步创建保证"工具返回成功 ⇔ 记录必已存在"，消除时序窗口；`start_run` 本就在 api.py（写库纪律天然合规）。快照复用 `views.execution_steps._build_case_snapshots`（函数级 import，同 App 内部）。

**D2：失败标记收敛为 `api.mark_run_failed(run_id, error, status)` 新函数。**
`views/ai_execution.py` 与 `views/helpers.py` 调用它（函数级 import 防循环），写库不出 api.py；状态用 `TestRunStatus.FAILED.value`/`STOPPED.value`（小写 canonical）。对 TaskCard 流（`client_task_id` 非空）不新增标记，维持状态机权威。

**D3：`_persist_run_start` AI 分支改为"复用已有记录升级"，而不是 update_or_create。**
预建的 PENDING 记录已含快照；执行真正启动时原地升级 `running` 并回填快照，保留 `started_at` 语义（投递时间即开始时间），避免重复创建撞唯一约束。

**D4：工具描述修正（P1）与代码同批。**
`run_test` 描述去掉"必须先 acquire_device"（实际自行锁设备），`get_run_status` 描述补 PENDING/FAILED 语义——防止模型沿用旧心智反复自锁/误解状态。

## 模块防火墙自检

- 写库收敛 api.py：预建与失败标记均在 `apps/test_runner/api.py`；device_pool 只改其自身 api.py 的比较逻辑。✅
- 跨 App import：AI 执行链新增调用为 test_runner 内部（api ↔ views，函数级 import）；不新增跨 App 依赖。✅
- 状态机：TaskCard 流不触碰；AI 路径本无 TaskCard，预建/升级/失败标记不经过 sm（与现状一致）。✅
- 前端/通道：无前端改动；不新增 WS/SSE 事件类型。✅

## Risks / Trade-offs

- [预建 PENDING 后，若进程崩溃在 PENDING 阶段会残留 PENDING 记录] → 孤儿回收（`recover_orphans`）已处理 RUNNING 残留，PENDING 残留与现状"零记录"相比仍是净改善；可后续纳入回收口径。
- [AI 并发重复 run_test 会在同一设备上叠加执行] → 不在本 change 范围；status 可见性提升后模型重复调用概率大降，必要时另开 change 做设备互斥。
- [`get_run_status` 历史数据大小写混杂] → 新写入统一小写，读侧透传原值，不影响既有消费方。
