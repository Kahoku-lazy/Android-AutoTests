## 1. 重试中间件

- [x] 1.1 新增 `engines/ae_harness/middleware/retry.py`：`is_transient_model_error(exc)`、`RetrySettings.load()`、`ModelRetryMiddleware`。验证：单测覆盖黑白名单分类
- [x] 1.2 非流式失败按退避重试，超过次数上抛原异常。验证：单测用替身计数，断言调用次数与最终异常
- [x] 1.3 流式只在首块之前重试；已产出后失败直接上抛。验证：单测构造「首块前抛错」与「产出后抛错」两种生成器
- [x] 1.4 退避参数走环境变量且有硬上限。验证：单测断言默认值、上限截断、非法值回退默认

## 2. 运行控制

- [x] 2.1 新增 `engines/ae_harness/middleware/control.py`：`RunBudget`、`CancelToken`、`BudgetExceeded`、`RunCancelled`。验证：单测断言两者是不同的异常类型
- [x] 2.2 `BudgetMiddleware`：每次模型调用前检查次数与时长，超限抛 `BudgetExceeded`。验证：单测设 1 次上限，第二次调用前抛出
- [x] 2.3 `CancelMiddleware`：每次模型调用前检查令牌，置位则抛 `RunCancelled`。验证：单测置位后下一次调用抛出
- [x] 2.4 不传预算/令牌时中间件不施加任何限制。验证：单测断言正常运行

## 3. 红线与文档

- [x] 3.1 `agents/AGENTS.md` 红线 2：从「唯一例外是只读观测」改为三类准入（只读观测 / 可靠性 / 运行控制），能力型仍禁止
- [x] 3.2 新增 `engines/ae_harness/middleware/AGENTS.md`：三类中间件的准入清单与禁止项
- [x] 3.3 `ae_harness/AGENTS.md` 登记两个新异常类（红线要求先立项）
- [x] 3.4 `middleware/__init__.py` 导出新中间件与异常

## 4. 接入平台

- [x] 4.1 `backend_bridge/session.py` 与 `workflow/roles.py` 接受可选 `budget` / `cancel`，挂到角色上。验证：单测断言不传时中间件列表与改造前一致
- [x] 4.2 `run_sop_once` 与 `run_ui_task` 透传这两个可选参数。验证：单测

## 5. 测试与门禁

- [x] 5.1 `python -m pytest -c tests/pytest.ini tests/engines/ae_harness tests/engines/backend_bridge -q` 全绿
- [x] 5.2 docstring / ruff 全过
- [x] 5.3 真机：给一次运行设 1 次调用预算，确认在第二次调用前中止且异常可识别
- [x] 5.4 `python run.py check` 与基线对比无新增失败
