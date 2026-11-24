# Proposal: fix-task-runtime-p0-defects

## Why

后端审计（2026-11-19）确认四处正在产生错误数据或安全暴露的运行时缺陷：心跳超时任务的费用被清零、设备锁身份可被请求体伪造、心跳遇瞬时 DB 故障永久停跳导致活任务被误收、清空任务绕过 api 导致截图文件泄漏。四项均已由 lead 逐行验证代码事实，属缺陷修复而非口径变更，需优先偿还。

## What Changes

- **费用回写改源**：`sweep_stale_tasks` 收口中断任务时，`rollup_task_cost` 不再聚合已退役的 `TaskEvent`（生产写点已消失，聚合恒 0），改从 usage_ledger 逐次账汇总该任务已产生费用回写 `cost_*`。
- **设备锁身份只信 JWT**：`lock_device` 删除 `request.data.get("user_id")` 回退分支，`locked_by` 只取 JWT 注入的 `request.user_id`；身份缺失时拒绝而非采信客户端。
- **心跳容错**：`_beat` 单次异常（含瞬时 DB 故障）不再置 `still=False` 永久停跳，改为记录日志并继续挂下一拍；任务收口仍由既有 sweep/claim_terminal 机制负责。
- **清空任务收敛进 api**：`AgentTaskClearAPIView` 改调 `api.clear_agent_tasks`（连带清理任务媒体文件），删除 View 内 `Task.objects.all().delete()` 直写；`task.result` 初始化下沉为 api 写原语。**保持现有清空范围（全平台）与响应契约不变**——权限面是否收紧属另行裁决项，不在本变更内。
- 同步修正上述路径的 docstring 与消费测试（含 `tests/task/unit/test_task_sweep.py` 等对事件费用口径的断言）。

## 关联文档

无新增 PRD 需求编号——本变更为缺陷修复，问题来源为后端审计报告（dev_docs/DEV_TEST/REVIEW-后端废弃代码与技术债审计.md）P0-1 / P0-3 / P0-4 / P0-5，四项均经 lead 亲验。费用回写改源是「恢复正确数据」：真实费用一直记录在 usage_ledger，任务表此前被恒写 0；不改变计费规则与 token 统计口径。

## Capabilities

### New Capabilities

- `device-lock-identity`: 设备锁/公开切换的身份来源契约——`locked_by` 只取自 JWT 注入身份，请求体不得伪造或覆盖。

### Modified Capabilities

- `task-execution-lifecycle`: 「重启后 running 记为中断」的费用回写来源从「事件明细」改为「平台逐次账（usage_ledger）」（事件表生产写点已随退役消失，原 requirement 已不可满足）；新增「工作线程心跳容错」requirement（瞬时故障不得永久停跳）。
- `task-list-module`: 清空任务 MUST 与单任务删除同口径清理任务媒体文件（现状绕过 api 导致文件泄漏）；接口路径与响应信封契约不变。

## Impact

- **backend/apps/task_list**：`api.py`（rollup_task_cost、sweep 调用点、result 写原语）、`task_runner.py`（_beat）、`views.py`（AgentTaskClearAPIView、result 初始化两处）。
- **backend/apps/device_pool**：`views.py` lock_device 一处。
- **backend/apps/usage_ledger**：只读消费其 api 的费用汇总口（如现有 `summarize_execution_cost`/`summarize_ledger_cost` 不满足按任务汇总，需在该 app api.py 增只读导出——跨 App 只调 api，合规）。
- **测试**：tests/task/unit/test_task_sweep.py、tests/task/unit/ 心跳相关用例、tests/device/api 锁定用例；新增费用回写与身份伪造回归用例。
- **不影响**：计费规则、token 口径、前端契约（响应形状不变）、engines。
- **协调**：usage_ledger 相关文件与已归档变更 fix-agentscope-usage-defects 无在途冲突（该变更已归档）；实施前仍需 `git pull` 核对工作树。