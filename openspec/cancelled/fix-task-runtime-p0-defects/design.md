# Design: fix-task-runtime-p0-defects

## Context

动机见 proposal.md - Why。四处缺陷的代码事实（审计时点亲验）：

- `task_list/api.py:1198 rollup_task_cost` 聚合 `TaskEvent(ModelCallEndEvent)`，但事件表生产写点已随退役消失（`insert_task_events` 全仓零调用）→ sweep（api.py:181）把中断任务 `cost_*` 恒写 0。真实费用在 usage_ledger；**同文件 :1181 已有现成只读口 `summarize_ledger_cost(task_id)`**（内部调 `usage_ledger.api.summarize_execution_cost(str(task_id), "task")`，账本不可用时返回 0+说明），正常完成路径 task_runner.py:535 已在用。
- `device_pool/views.py:348 lock_device` 身份回退请求体。`/api/devices/*` 非公开路径，JWT 中间件已先行鉴权；回退分支是唯一伪造面。
- `task_list/task_runner.py:305-322 _beat`：except 置 `still=False` → 不再挂下一拍计时器。进程真死时计时器本就随进程消失，sweep 兜底不受影响；因此「异常即停跳」只有坏处没有好处。
- `task_list/views.py:291` View 直写 `Task.objects.all().delete()`；`api.clear_agent_tasks`（api.py:701）已实现删行+清理媒体，全仓零调用。views.py:90-91、151-152 另有两处 View 内 `task.save(update_fields=["result"])`。

约束：写库走 api.py；跨 App 只调对方 api.py；不改计费规则与 token 口径；清空范围（全平台）与响应契约保持不变（权限面收紧属另行裁决项）。

## Goals / Non-Goals

**Goals**
- 中断任务费用按账本正确回写；心跳瞬时故障可自愈；锁身份不可伪造；清空不再泄漏媒体文件。
- 四项修复各配回归测试，进入默认 unit/integration 套件（不依赖 collect-only 之外的显式开关）。

**Non-Goals**
- 不删除 TaskEvent 表/模型与 `insert_task_events` 等死函数（属 retire-backend-dead-code 变更；本变更只让 rollup 不再读它）。
- 不改清空端点的权限面（全平台删除现状保留，是否限超管/按用户过滤待需求方另行裁决）。
- 不动计价双轨、评测 0 token 等钱口径问题（属 fix-eval-usage-billing 变更）。
- 不重构 device_pool 写路径整体收敛（属 converge-device-pool-writes-to-api 变更；本变更只修 lock_device 身份一行）。

## Decisions

### D1 费用回写复用 `summarize_ledger_cost`，不新建汇总口
`rollup_task_cost` 改为调同模块 `summarize_ledger_cost(task_id)` 取 totals 回写 `cost_*`；notes 非空时记 warning 日志（含「账本暂时不可用」情形）。
- 备选：在 usage_ledger 新增按任务汇总 API——多余，现成口已满足且正常完成路径同源，两条收口路径口径天然一致。
- 顺带修 `summarize_ledger_cost` 的 except 分支补 `backend_log.exception`（审计 T 项「吞异常无日志」，一行改动，与本缺陷同链路）。
- 保留函数名 `rollup_task_cost` 与调用点不动，diff 最小。

### D2 心跳异常改为「记日志 + 继续下一拍」
`_beat` 的 except 分支不再置 `still=False`，改为 `still=True`（或直接调度下一拍）。
- 理由：终态检测下一拍会重做，DB 恢复后自然停；进程真死时 daemon 计时器随进程消失，sweep 45 秒兜底语义不变。无需「连续 N 次失败才停」的计数器——停跳的正当场景（终态/线程退出）已有独立检测与 `stop_heartbeat`。
- 备选：失败计数阈值——引入新状态与魔法值，收益为零，弃。

### D3 锁身份删除回退 + 显式空身份守卫
`lock_device` 只取 `getattr(request, "user_id", "")`；为空时返回 401（中间件正常工作时不可达，属防御性守卫，满足 spec「无鉴权身份拒绝落锁」）。请求体 `user_id` 字段直接忽略（不报 400，保持对旧客户端宽容——字段被忽略而非报错，契约形状不变）。

### D4 清空收敛调 api；result 初始化下沉写原语
- `AgentTaskClearAPIView.post` 改调 `api.clear_agent_tasks()`，响应形状不变。
- views.py 两处 `task.result = …; task.save(...)` 下沉为 `api.init_task_result(task_id, payload)` 写原语（内部 `merge_task_result` 已有合并语义，复用之），View 只分发。
- 备选：把 result 初始化并入 create_task 参数——改动面更大且涉及提交契约，弃。

## Risks / Trade-offs

- [账本不可用时中断任务费用仍暂记 0] → 与正常完成路径同口径（fail-open + notes 说明 + 日志），不阻断收口；账本恢复后可经既有 `recalc_usage_costs` 运维命令回填，无需新机制。
- [心跳在 DB 长期故障期间每 15 秒空转重试] → daemon 计时器开销可忽略；线程退出时 `stop_heartbeat` 清理；日志可观测。
- [清空改调 api 后媒体清理增加 IO] → 与单任务删除同口径，属修复预期行为；大批量时逐任务清理，耗时可接受（调试端点低频）。
- [旧客户端依赖请求体 user_id 落锁] → 全仓 grep 前端 lock 调用只发 `{locked}`，无此依赖；忽略字段不报错，兼容。

## Migration Plan

纯代码修复，无迁移、无配置变更。部署即生效；回退 = 还原对应提交。历史已被清零的中断任务费用不在本变更自动回填（如需回填，运维按账本执行既有重算命令，属运维动作不入代码）。

## Open Questions

无。清空权限面、TaskEvent 表退役、钱口径均已明确划出本变更（见 Non-Goals），不影响本设计的规格与任务拆分。