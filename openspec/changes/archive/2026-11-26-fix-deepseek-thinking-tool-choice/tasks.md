## 1. 引擎：重发守卫抽共用并扩到 deepseek

- [x] 1.1 在 `engines/ae_harness/agents/models.py` 抽出共用重发守卫（mixin），把 `OpenAIGatewayChatModel._call_api` 的三步逻辑搬进去，行为保持不变；验证：`ruff check engines/ae_harness/agents/models.py` 通过，并用 `temps/` 脚本注入假客户端复跑 openai 三支（普通 400 不重发、关思考重发、收窄结构化工具）结果与改动前一致
- [x] 1.2 新增 deepseek 包装类（继承共用守卫与 `DeepSeekChatModel`），并在 `create_model` 的 `provider == "deepseek"` 分支返回它，其余参数口径不变；验证：`python -c "from engines.ae_harness.agents.models import create_model; print(type(create_model('deepseek','DEEPSEEK_API_KEY','deepseek-flash').model).__name__)"` 打印包装类名，`temps/` 脚本断言三次请求的 `tool_choice`、工具清单与 `extra_body.thinking.type`
- [x] 1.3 导出公开判定函数 `is_thinking_tool_choice_rejection(exc)` 并加入 `__all__`，供后端识别失败类型；验证：`ruff check` 通过，`temps/` 脚本断言行内含该句时返回真、普通 400 返回假

## 2. 引擎：abort 回调携带用量快照

- [x] 2.1 修改 `engines/backend_bridge/workflow/bound_sop.py`：`_SopCapture.abort` 在写报告的同时返回 `tokens`、`usages`、`cost_s`、`model` 快照，`on_abort` 回调增加该参数，异常仍原样抛出；验证：`tests/arch/unit/test_sop_report_contract.py` 通过，`temps/` 脚本构造一次中断断言回调收到非空 `usages`
- [x] 2.2 更新受签名影响的调用方与用例：`backend/apps/task_list/task_runner.py` 的 `_remember`、`tests/task/integration/test_task_failure_report.py` 的假回调；验证：`python -m pytest -c tests/pytest.ini tests/task/integration/test_task_failure_report.py tests/arch/unit/test_sop_report_contract.py` 通过

## 3. 后端：失败收口写逐次账与任务用量

- [x] 3.1 把 `task_runner._record_task_usages` 改为接收 `usages` 与 `model`，成功路径传 `outcome.usages` / `outcome.model`，行为不变；验证：`python -m pytest -c tests/pytest.ini tests/task` 通过
- [x] 3.2 失败分支使用回调快照写逐次账、用 `api.summarize_ledger_cost` 汇总并 `claim_terminal(usage=..., costs=...)`，逐次账不可写时不阻断终态；验证：扩展 `tests/task/integration/test_task_failure_report.py`，构造「先回调带 2 条用量再抛错」的假运行，断言任务 token 与费用非 0、`ai_usage_records` 有该执行 ID 的行，且再触发一次收口费用不翻倍

## 4. 后端：交卷轮失败文案

- [x] 4.1 `backend/apps/task_list/api.py` 的 `category_step` 增加可选 `name` 参数（不传保持原映射），`task_runner._failure_payload` 在 `provider` 且命中 `is_thinking_tool_choice_rejection` 时写「交卷轮被思考模式拒绝（400）」并把步骤名传为「交卷轮被拒绝」；验证：`tests/task/integration/test_task_failure_report.py` 新增两条断言——命中时 `reason`、`summary`、`failed_steps[0].name` 符合规格，未命中时仍是「模型拒绝（状态码）」
- [x] 4.2 确认 `failed_steps[0].kind` 仍为 `provider`、状态仍为 `failed`，且重发成功路径不产生失败步骤；验证：同一集成用例覆盖，`python -m pytest -c tests/pytest.ini tests/task/integration/test_task_failure_report.py` 通过

## 5. 门禁与人工验收

- [x] 5.1 跑后端门禁：`python manage.py check`、`ruff check`、`python -m pytest -c tests/pytest.ini tests/task/integration tests/arch/unit/test_sop_report_contract.py tests/report/integration`、`python utils/gen_arch_stats.py --check-boundaries`；本变更相关用例全绿，`tests/task` 与 `tests/arch/unit` 中与本变更无关的既有失败（提交用例的 `Workflow.release_state`、`engines/agents` 已退役等）单独记录
- [x] 5.2 真机复跑：用同一用例（H6810 场景功能测试）重跑一条任务，确认第 20 轮后的强制交卷不再整单失败；若模型仍在交卷轮被拒，任务 `result` 与报告应写明「交卷轮被思考模式拒绝（400）」，且 task 的 token/费用不为 0（任务 261：4/4 步通过，173.3 s，922,817 input / 14,268 output tokens，费用 0.19087140，逐次账 52 行，期间一次 400 被守卫重发后继续；复跑任务 263：3 次强制交卷 400 均被重发接住，任务按 `verdict` 在第 3/4 步失败而非 `provider`，费用 0.44973412、逐次账 91 行；据此修订用例 `TC-20261117-0004` 的第 2/3 步后，任务 264 以 4/4 步通过，119.5 s，667,494 input / 11,851 output tokens，费用 0.13937928）
- [ ] 5.3 回归确认：成功任务与既有 openai 通道任务行为不变（本次已用任务 261 覆盖成功任务；openai 通道真实调用待有 `OPENAI_API_KEY` 时补，代码路径与 deepseek 共用同一个守卫 mixin）

## 6. 文档同步

- [x] 6.1 更新 `.agents/docs/apps/task_list/task_list_task_lifecycle.md`（失败收口也写逐次账与任务用量、`cancelled`/`interrupted` 仍不在范围）；验证：人工核对与 `task_runner` 实现一致
- [x] 6.2 更新 `.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md`（abort 回调携带用量快照）与 `.agents/docs/engines/ae_harness_agents/ae_harness_agents_agent_creation.md`（openai 与 deepseek 共用重发规则、新增公开判定函数）；验证：`git diff --check` 与人工核对
