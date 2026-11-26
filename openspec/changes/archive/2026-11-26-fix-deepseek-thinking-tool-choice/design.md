## Context

- `engines/ae_harness/agents/models.py` 目前只在 `provider=openai` 分支把 `OpenAIChatModel` 包成 `OpenAIGatewayChatModel`，由它实现「思考模式拒绝强制 `tool_choice`」的重发；`provider=deepseek` 直接返回框架的 `DeepSeekChatModel`，同一句 400 没有兜底。
- 框架在回复内 `cur_iter >= max_iters` 时会把 `tool_choice` 强制为 `GenerateStructuredOutput`（`engines/backend_bridge/agents/run_params.py` 把 `MAX_ITERS` 设为 20）。这次失败发生在第 20 轮工具调用之后的那次强制交卷请求上，请求在执行前被 400 拒绝。
- `engines/backend_bridge/workflow/bound_sop.py` 的 `on_abort(report_path, exc)` 只把报告路径交给调用方；`record` 里已有的 `usages` / `cost_s` 在异常抛出后丢失。
- `backend/apps/task_list/task_runner.py` 的失败分支只写状态、`result` 与 `finished_at`，不调用 `claim_terminal(usage=..., costs=...)`，也不写逐次账；成功分支才走 `_record_task_usages` 与 `api.summarize_ledger_cost`。
- 任务 260 的失败文案由 `_failure_payload` 按 `openai` 异常的 `status_code` 生成「模型拒绝（400）」，`failed_steps` 的名称来自 `api.category_step("provider", ...)` 的固定映射。
- 任务详情页已于 2026-11-26 退役（提交 `5ddebe95`，前端不再有 `/tasks/:id` 路由，`/api/tasks/{id}/` 仍保留）；本变更的可观察面是 `Task.result`、`/api/reports/` 台账与 BUG 单，不是页面。

## Goals / Non-Goals

**Goals:**

- deepseek 通道获得与 openai 通道完全一致的重发语义（同一句 400、仅强制工具、最多一次、先关思考、按需收窄工具集）。
- 失败收口不丢账：本次运行已结束的模型调用进入逐次账，任务 token 与费用按整次运行累计值回写。
- 交卷轮 400 的失败原因可辨认，不再与密钥/额度类失败混在一起。

**Non-Goals:**

- 不预先关闭交卷轮的思考，也不调整 `MAX_ITERS` / 宽限轮次（会改变成本与成功口径，另开变更）。
- 不改 dashscope 通道，不给通用 400 增加重试。
- 不改 `engines/agents`（已不存在）与任何「30 次后强制关思考」的历史规格。
- 不回填历史失败任务的用量与费用。
- 不处理用户取消（`cancelled`）、预算超限或进程退出（`interrupted`）的用量回写；取消沿用既有口径，进程退出已有启动恢复，预算中断的用量另议。
- 不处理 `goal` / `team` 编排链路的用量与费用回写（它们当前成功收口也不写逐次账，另开变更）。
- 不处理 `task_events` 当前没有任何落库行的问题（与本次三条规格无关，另行排查）。
- 不恢复任务详情页；验收只认任务记录、报告台账与 BUG 单。

## Decisions

### D1 把重发逻辑抽成共用守卫，两条通道各包一层

在 `models.py` 内抽一个 mixin（例如 `ThinkingToolChoiceGuard`），实现现有的 `try / 关思考重发 / 收窄工具集` 三步，`OpenAIGatewayChatModel` 与新增的 deepseek 包装类都只继承该 mixin 与各自框架模型。`super()._call_api(...)` 在 mixin 内解析到具体框架类，无需复制实现。

备选：
- 复制一份 deepseek 版本：两条通道的规则会各自漂移，已出现过「只修 openai」的漏项，否决。
- 在 Agent 中间件改 `tool_choice`：观测/控制中间件不允许改请求参数，且这次失败在中间件之后，否决。
- 直接给 `DeepSeekChatModel` 传 `thinking_enable=False`：等于全程关思考，伤正常轮次的判断质量，且规格要求只在被拒时关，否决。

### D2 deepseek 包装只在 `create_model` 的 deepseek 分支挂载

`create_model` 的 `provider == "deepseek"` 分支返回包装后的模型，类名与现有 `OpenAIGatewayChatModel` 对齐（例如 `DeepSeekToolChoiceChatModel`）。`api_key_env`、`stream`、`max_retries`、formatter 与 `_input_types` 的取值保持现状，避免影响非交卷轮。

### D3 abort 回调携带用量快照，不新增异常类型

`run_bound_sop` 的 `on_abort` 增加第三个参数（用量快照 dict：`tokens`、`usages`、`cost_s`、`model`），由 `_SopCapture.abort` 在写报告时一并产出。异常仍原样抛出。

备选：
- 新增 `SopAbortedError` 携带 usages：`engines/` 红线禁止随意新增自定义异常类，需要先立项，成本高，否决。
- 任务执行方 abort 后读 `aligned.json` 的 `summary.usages`：把读报告文件当成账本来源，报告写失败时用量就丢；职责也不对，否决。

### D4 失败收口复用 `claim_terminal` 的用量与费用入口

`task_runner` 的失败分支在拿到用量快照后：先按 `task:<task_id>:<round>` 写逐次账（与成功路径同一个 `record_run_usages`），再用 `api.summarize_ledger_cost(task_id)` 汇总，最后 `claim_terminal(..., usage=_usage_totals(tokens), costs=costs)`。`_record_task_usages` 改为接收 `usages` 列表与 `model`，成功路径传 `outcome.usages` / `outcome.model`。

用整次运行的累计值回写而不是累加，是因为 `api._apply_usage` 是覆盖式写入，重入不会翻倍；逐次账由 `record_usage` 按 `event_id` 幂等更新。该路径只覆盖 `assistant_sop`（`run_bound_sop` 的 on_abort 快照）；`_finish_goal` / `_finish_team` 没有用量快照，保持现状。

### D5 文案判定放在引擎的公开 helper，步骤名可覆写

`models.py` 暴露 `is_thinking_tool_choice_rejection(exc)`（判断文案含该句），`task_runner._failure_payload` 在 `kind == "provider"` 且命中时把 `reason` / `summary` 写成「交卷轮被思考模式拒绝（400）」。`api.category_step(kind, actual)` 增加可选 `name` 参数，失败时传「交卷轮被拒绝」；不传时保持原映射，避免影响其它失败。

### D6 规格边界：这是窄口径重发，不是通用重试

`agent-model-resilience` 的「400 MUST NOT 重试」继续适用于瞬态重试链路；本次只在「请求未执行、且本次强制了工具」时重发，与既有 openai 口径完全一致，不改变瞬态重试的次数上限（模型层 2 次 × 中间件 3 次）。

## 模块防火墙自检

- 跨 App import：`task_runner` 只使用本 App 的 `api.claim_terminal` / `api.summarize_ledger_cost` / `api.category_step`，逐次账经 `backend.apps.usage_ledger.api.record_run_usages`，无跨 App 内部实现 import。
- 写库：任务与费用仍全部收敛在 `task_list/api.py` 与 `usage_ledger/api.py`，引擎侧只产用量快照，不碰 ORM。
- 依赖方向：`backend/` → `engines/`（允许）；`engines/` 不反向 import `backend.*`，`backend_bridge` 不 import `apps.*`。
- 异常：不新增自定义异常类，沿用框架的 `openai.BadRequestError`。
- 前端：无改动，`/api/tasks/{id}/` 响应形状不变。

## Risks / Trade-offs

- [重发可能让模型重复执行设备动作] → 只在这句 400 出现时重发，而该错误发生在请求执行前；普通工具轮与 `auto` 选择不重发。第二次重发收窄到只留结构化工具，物理上无法再点设备。
- [交卷轮请求成本 +1 次] → 仅在被拒时发生，且只发生在轮次用尽的重负载回复上；相比整单失败重跑，成本更低。
- [abort 时报告尚未建立（recorder 为空）] → 用量快照为空，任务用量保持 0 并留日志；这是可接受的退化，不影响终态落库。
- [`GenerateStructuredOutput` 工具名随框架升级改名] → `_forced_name` 与收窄逻辑都会失效；在 design 与测试里锁定常量，升级 AgentScope 时按 `models.py` 的常量核对。
- [失败任务重入] → 用量用整次累计值覆盖写入，逐次账按 `event_id` 幂等，不会翻倍。
- [历史失败任务仍是 0 用量] → 本变更不回填；如需回填，按 `logs/agents/**/aligned.json` 的 `summary.usages` 另开一次性迁移。

## Open Questions

- `govee-thinking-tool-choice` 主规格的 Purpose 目前仍写「约束 OpenAI 网关」；归档本变更时需同步改成「openai 与 deepseek 通道」，否则目的段与需求范围不一致。
- 用户取消（`cancelled`）是否也要回写用量与费用：本次按 Non-Goals 不动，待确认后再单开变更。
