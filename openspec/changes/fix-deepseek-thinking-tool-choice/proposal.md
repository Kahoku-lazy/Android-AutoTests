## Why

2026-11-25 18:21–18:24，任务 255 / 256 / 259 / 260 在设备动作已经执行、只差交结论时整单失败：执行器同一回复跑满 20 个推理轮次后，框架强制 `tool_choice=GenerateStructuredOutput`，而 `deepseek-flash` 处于思考模式，DeepSeek 接口以 `400 Thinking mode does not support this tool_choice` 拒绝。同一条重发规则目前只包了 openai 网关通道（`govee-thinking-tool-choice`），deepseek 通道没有任何兜底，错误原样抛出后任务被记为「模型拒绝（400）」。同时，失败任务没有回写已发生的模型调用用量：260 实耗约 30.7 万 input tokens，任务记录仍是 0；详情页也因此只能看到一句笼统文案，无法判断失败发生在交卷轮。

## What Changes

- deepseek 通道套用与 openai 网关相同的重发规则：只在收到含 `Thinking mode does not support this tool_choice` 的 400、且本次请求强制了工具时重发；其余 400、超时、连接失败不重发；同一次调用最多重发一次。
- 强制交卷时先关闭思考并保持强制同一个工具；若关思考后仍是这句 400，再只保留结构化交卷工具并把选择权交回模型（`auto`），请求不再携带设备工具。强制设备工具的轮次只关思考、不改工具名；禁止调用工具的轮次只关思考、继续禁止。
- 失败收口仍要把本次运行已经发生的模型调用写入逐次账，并按执行 ID 回写任务的 token 与费用列；abort 回调需要把用量快照一并交给任务执行方，不再只交报告路径。
- 交卷轮被思考模式拒绝且重发后仍然失败时，任务失败原因写明「交卷轮被思考模式拒绝（400）」，步骤名与 `actual` 同步改写，不再笼统写「模型拒绝（400）」。

## 关联文档

无 PRD 条目：本改动来自 2026-11-25 现场故障（任务 255 / 256 / 259 / 260 在交卷轮 400 失败，任务 260 实耗 306,807 input tokens 却记 0）的排障结论，属缺陷修复与既有规格补齐，不对应 `PRD-平台总需求.md` 中的需求编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `govee-thinking-tool-choice`: 「只重发这一种未执行的 400」由 openai 通道扩到 deepseek 通道，dashscope 仍不套用；「关思考参数经官方扩展点声明」同步覆盖 deepseek。
- `agent-task-event-store`: 新增「异常收口也写逐次账与任务用量」，要求失败收口与成功收口一样汇总已发生的模型调用。
- `sop-task-run`: 新增「交卷轮被模型拒绝时失败原因写明交卷轮」，约束失败文案与步骤快照的写法。

## Impact

- 引擎：`engines/ae_harness/agents/models.py`（重发规则从 openai 通道抽成共用实现并挂到 deepseek 通道）、`engines/backend_bridge/workflow/bound_sop.py`（abort 回调携带用量快照）。
- 后端：`backend/apps/task_list/task_runner.py`（失败收口写用量与费用、失败文案识别）、`backend/apps/task_list/api.py`（步骤快照名称可覆写）。
- 数据：`task_tasks` 的 `input_tokens` / `output_tokens` / `cache_input_tokens` / `cost_*` 在失败任务上不再恒为 0；`ai_usage_records` 新增失败运行的调用行。无迁移。
- 接口：`/api/tasks/{id}/` 响应形状不变，仅 `result` 内的文案与用量取值变化。
- 测试：扩展 `tests/task/integration/test_task_failure_report.py`；不新增 `tests/**/unit/`（按 `tests/AGENTS.md` 口径），引擎侧重发行为用 `temps/` 脚本实测后丢弃。
