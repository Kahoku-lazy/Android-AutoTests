## 1. 观测中间件（不接入口）

- [x] 1.1 新增 `engines/ae_harness/middleware/observer.py`：观测记录数据类（`kind`、绝对时间、耗时）+ `ObservationMiddleware`，构造接受可选 `emit` 回调，不传写自有 `records`。验证：`python -c "from engines.ae_harness.middleware.observer import ObservationMiddleware"` 成功
- [x] 1.2 实现 `on_system_prompt`：记录全文与长度后**原样返回**。验证：单测断言返回值与入参逐字符相同、记录里文本一致
- [x] 1.3 实现 `on_compress_context`：调用前读 `agent.state.context` 条数与阈值参数，`await next_handler(...)` 后再读一次，记录是否压缩、前后条数、比例/窗口/阈值、指令文本、耗时。验证：单测用替身 agent 断言「未压缩 / 压缩」两种记录
- [x] 1.4 中间件不实现 `list_tools`、不实现能力型 hook。验证：单测断言 `is_implemented("list_tools")` 为假、`is_implemented("on_compress_context")` 与 `on_system_prompt` 为真
- [x] 1.5 `middleware/__init__.py` 导出观测中间件与记录类型。验证：`from engines.ae_harness.middleware import ObservationMiddleware` 成功

## 2. 装配：角色创建出口与事件层

- [x] 2.1 `agents/creator.py` 增加仅关键字入参 `observers`（默认空），内部只作为 `Agent(middlewares=...)` 透传；`agents/` 不 import `middleware`。验证：单测断言传入的中间件实例出现在智能体上、不传时与改造前一致
- [x] 2.2 `event/record.py` 的 `AgentEventRecorder` 增加仅关键字入参 `observations`（默认空），并在 `finish()` 时把观测记录写进 JSONL、挂到 `RunRecord.observations`。验证：单测断言 JSONL 出现观测行且 `event` 字段与其他行不同
- [x] 2.3 观测行不与既有事件行混淆：类型字段固定、带 `kind` 子字段。验证：单测断言行结构
- [x] 2.4 `agents/AGENTS.md` 的「装配方式」补上实际入参名 `observers` 与「一次运行只挂一个」。验证：人工核对文档与代码一致

## 3. 入口接入

- [x] 3.1 `assistant/agent_executor.py`：建观测中间件 → 传给 `create_agent` → 把其记录列表交给记录器。验证：入口实跑后 JSONL 出现 `system_prompt` 观测行
- [x] 3.2 `assistant/agent_verifier.py` 同上。验证：同上
- [x] 3.3 `workflow/sop/runner.py` 的 `run_sop` 增加带默认值的观测参数并透传。验证：不传时 SOP 行为与产物不变
- [x] 3.4 `workflow/sop_runner.py` 接入观测中间件。验证：混跑后 JSONL 同时出现两类观测行（多轮 system prompt）

## 4. 测试与守卫

- [x] 4.1 新增 `tests/engines/ae_harness/unit/test_observer.py`：透传一致、压缩两态、无 `list_tools`、`emit` 回调与默认容器两条投递路径。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness -q` 全绿
- [x] 4.2 扩展导入守卫：断言 `middleware/` 下模块无任何 `engines.ae_harness.*` 同包导入、无 `django` / `backend`。验证：守卫用例通过；故意加一句同包导入时失败
- [x] 4.3 回归断言：不挂观测中间件时，JSONL 行类型集合与改造前一致。验证：单测比较行类型集合

## 5. 门禁与收尾

- [x] 5.1 `python -m scripts.docstrings check --path engines/ae_harness` 归零。验证：0 error / 0 warn
- [x] 5.2 `ruff check` 与 `ruff format --check`（engines/ae_harness + tests/engines/ae_harness）全过。验证：退出码 0
- [x] 5.3 `.agents/skills/engines-agents-style-check` 确认新增文件不引入新告警。验证：新增文件无命中
- [x] 5.4 `python run.py check` 与基线对比，确认没有新增失败项。验证：失败项集合与基线一致
- [x] 5.5 导入冒烟：walk 全部子模块并 import，0 失败。验证：输出「失败模块数: 0」
