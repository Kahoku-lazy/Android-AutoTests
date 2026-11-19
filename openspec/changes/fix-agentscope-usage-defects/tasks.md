# Tasks: fix-agentscope-usage-defects

## 1. P0 权限缺陷修复（tools 域）

- [x] 1.1 `engines/ae_harness/tools/document/tools.py`：`_ALLOW` 由 lambda 改为 `PermissionDecision(behavior=ALLOW, message=...)` 实例（对齐 adb 域写法），同步模块 docstring 版本/修改时间；验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge/unit/test_tool_selection.py -q` 通过
- [x] 1.2 `engines/ae_harness/tools/case_library/tools.py`：同 1.1 改法；验证：同上测试通过
- [x] 1.3 新增单测 `tests/engines/ae_harness/unit/test_tool_permission.py`：断言 `save_authored_case` 与 `read_requirement` 的 `check_permissions()` 返回 `PermissionDecision` 实例且 behavior=ALLOW、不是可调用对象（对应 harness-tool-permission 三个 Scenario）；验证：新测试通过

## 2. 重试单层化（agents/models）

- [x] 2.1 `engines/ae_harness/agents/models.py`：`create_model` 新增关键字参数 `max_retries: int = 1`，透传 DeepSeek/DashScope/openai 三家构造器；docstring 补 Args 与简介条目、版本/修改时间；`create_agent` 签名不动；验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_creator.py tests/engines/ae_harness/unit/test_retry_middleware.py -q` 通过
- [x] 2.2 新增/更新单测：默认 `create_model` 产出模型 `max_retries == 1`；显式传 0 时产出模型 `max_retries == 0`（对应 agent-model-resilience 分层 Scenario）；验证：新测试通过

## 3. openai 官方扩展点（agents/models）

- [x] 3.1 `OpenAIGatewayChatModel` 增加 `_get_disable_thinking_kwargs()` 覆写，返回 `{"extra_body": {"thinking": {"type": "disabled"}}}`；`_call_api` 兜底原样保留；模块 docstring 简介补条目；验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_openai_message_name.py tests/engines/ae_harness/unit/test_openai_tool_choice.py -q` 通过
- [x] 3.2 新增单测：断言扩展点返回值形状，且普通 400 仍只发一次（对应 govee-thinking-tool-choice 新增 Scenario，能力路径沿用旧名）；验证：新测试通过

## 4. SOP 角色归属与尝试序号（event + workflow/sop）

- [x] 4.1 `engines/ae_harness/event/record.py`：`AgentEventRecorder` 新增可选入参 `sop_roles`；`ReplyStartEvent` 有映射按 agent 名归属、无映射沿用奇偶推断；`SOP_STEP_STARTED` 读取 `value.attempt` 存 `_sop_attempt`；`StepRecord` 新增 `sop_attempt: int = 0` 并在工具记录写入；docstring 同步；验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_record_usage.py tests/engines/ae_harness/unit/test_record_full.py tests/engines/ae_harness/unit/test_report_render.py -q` 通过
- [x] 4.2 `engines/ae_harness/workflow/sop/runner.py`：`run_sop` 构造 `sop_roles={executor.name: "executor", verifier.name: "verifier"}`（getattr 取 name）传入 recorder；docstring 同步；验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge/unit/test_bound_sop.py -q` 通过
- [x] 4.3 新增单测：有映射时乱序回复归属正确、无映射时奇偶兜底不变、第 2 次尝试的工具记录带 `sop_attempt=2`（对应 ae-harness-event-full-record 新增 Scenario）；验证：新测试通过
- [x] 4.4 更新 `engines/ae_harness/workflow/AGENTS.md`「已知限制 2」为名字映射口径（非红线条款，事实描述同步）；验证：文档与 4.1/4.2 实现一致

## 5. 门禁与交付

- [x] 5.1 docstring 自检：`cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check`（git 改动范围）零新增 error；风格自检：`cd .agents/skills/engines-agents-style-check && python -m scripts.check_engines_agents_style` 通过
- [ ] 5.2 本地门禁 `python run.py check` 通过；定向回归 `python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit tests/engines/backend_bridge/unit -q` 全绿
- [ ] 5.3 逐件提交（禁 `git add -A`）：`fix(tools): 工具权限放行改传决策实例`、`fix(agents): 模型层重试默认收敛为 1 避免与中间件叠加`、`feat(agents): openai 关思考接入官方扩展点`、`fix(event): SOP 角色归属按名字映射并记录尝试序号`，OpenSpec 工件随对应提交或单独 `docs(openspec)` 提交；推送 `Kahoku` 后确认 `ci-phase1.yml` 的 python 与 frontend 两个 job 全绿