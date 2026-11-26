## 1. 引擎：重发守卫抽共用并扩到 deepseek

- [ ] 1.1 在 `engines/ae_harness/agents/models.py` 抽出共用重发守卫（mixin），把 `OpenAIGatewayChatModel._call_api` 的三步逻辑搬进去，行为保持不变；验证：`ruff check engines/ae_harness/agents/models.py` 通过，并用 `temps/` 脚本注入假客户端复跑 openai 三支（普通 400 不重发、关思考重发、收窄结构化工具）结果与改动前一致
- [ ] 1.2 新增 deepseek 包装类（继承共用守卫与 `DeepSeekChatModel`），并在 `create_model` 的 `provider == "deepseek"` 分支返回它，其余参数口径不变；验证：`python -c "from engines.ae_harness.agents.models import create_model; print(type(create_model('deepseek','DEEPSEEK_API_KEY','deepseek-flash').model).__name__)"` 打印包装类名，`temps/` 脚本断言三次请求的 `tool_choice`、工具清单与 `extra_body.thinking.type`
- [ ] 1.3 导出公开判定函数 `is_thinking_tool_choice_rejection(exc)` 并加入 `__all__`，供后端识别失败类型；验证：`ruff check` 通过，`temps/` 脚本断言行内含该句时返回真、普通 400 返回假

## 2. 引擎：abort 回调携带用量快照

- [ ] 2.1 修改 `engines/backend_bridge/workflow/bound_sop.py`：`_SopCapture.abort` 在写报告的同时返回 `tokens`、`usages`、`cost_s`、`model` 快照，`on_abort` 回调增加该参数，异常仍原样抛出；验证：`tests/arch/unit/test_sop_report_contract.py` 通过，`temps/` 脚本构造一次中断断言回调收到非空 `usages`
- [ ] 2.2 更新受签名影响的调用方与用例：`backend/apps/task_list/task_runner.py` 的 `_remember`、`tests/task/integration/test_task_failure_report.py` 的假回调；验证：`python -m pytest -c tests/pytest.ini tests/task/integration/test_task_failure_report.py tests/arch/unit/test_sop_report_contract.py` 通过

## 3. 后端：失败收口写逐次账与任务用量

- [ ] 3.1 把 `task_runner._record_task_usages` 改为接收 `usages` 与 `model`，成功路径传 `outcome.usages` / `outcome.model`，行为不变；验证：`python -m pytest -c tests/pytest.ini tests/task` 通过
- [ ] 3.2 失败分支使用回调快照写逐次账、用 `api.summarize_ledger_cost` 汇总并 `claim_terminal(usage=..., costs=...)`，逐次账不可写时不阻断终态；验证：扩展 `tests/task/integration/test_task_failure_report.py`，构造「先回调带 2 条用量再抛错」的假运行，断言任务 token 与费用非 0、`ai_usage_records` 有该执行 ID 的行，且再触发一次收口费用不翻倍

## 4. 后端：交卷轮失败文案

- [ ] 4.1 `backend/apps/task_list/api.py` 的 `category_step` 增加可选 `name` 参数（不传保持原映射），`task_runner._failure_payload` 在 `provider` 且命中 `is_thinking_tool_choice_rejection` 时写「交卷轮被思考模式拒绝（400）」并把步骤名传为「交卷轮被拒绝」；验证：`tests/task/integration/test_task_failure_report.py` 新增两条断言——命中时 `reason`、`summary`、`failed_steps[0].name` 符合规格，未命中时仍是「模型拒绝（状态码）」
- [ ] 4.2 确认 `failed_steps[0].kind` 仍为 `provider`、状态仍为 `failed`，且重发成功路径不产生失败步骤；验证：同一集成用例覆盖，`python -m pytest -c tests/pytest.ini tests/task/integration/test_task_failure_report.py` 通过

## 5. 门禁与人工验收

- [ ] 5.1 跑后端门禁：`python manage.py check`、`ruff check`、`python -m pytest -c tests/pytest.ini tests/task tests/arch`、`python utils/gen_arch_stats.py --check-boundaries` 全部通过
- [ ] 5.2 真机复跑：用同一用例（H6810 场景功能测试）重跑一条任务，确认第 20 轮后的强制交卷不再整单失败；若模型仍在交卷轮被拒，任务详情应显示「交卷轮被思考模式拒绝（400）」且 token/费用不为 0
- [ ] 5.3 回归确认：成功任务与既有 openai 通道任务行为不变（成功 254 同类用例复跑一次，费用与步骤结论与改动前口径一致）
