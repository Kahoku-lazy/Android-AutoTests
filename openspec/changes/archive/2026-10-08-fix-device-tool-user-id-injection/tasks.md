## 1. 修复

- [x] 1.1 工具包装层改为「按签名注入 `user_id`」：仅当被包装函数声明了该参数时才补；参数表剥离逻辑不变。验证：断言「声明 user_id 的函数收到注入值」「未声明的函数不被注入」，且既有工具包装相关用例全绿。**验证结果**：自检输出 `with -> got user_id='42'` / `without -> no user_id needed`，两者参数表均不含 `user_id`；相关最小集（模型调试 / 角色工具子集 / 平台工具调试 / 通信通道）54 通过 + 1 跳过。
- [x] 1.2 真机跑测复验：用 `tests/engines/test_executor_steps.py` 跑示例步骤，确认引擎自带设备动作工具不再报 `user_id` 错误、每步都有成功的工具返回与截图路径。验证：跑测输出中工具返回状态为成功、无该错误文本。**验证结果**：修复前 3 步全为 error 且报 `got an unexpected keyword argument 'user_id'`（8 次调用全失败、费用 0.010623 白烧）；修复后 3 步全成功、工具返回 `状态=success`、每步都有截图路径（留档 `temps/harness_run2.txt`）。

## 2. 关单

- [x] 2.1 复核与汇报：`apps/` 与前端零改动；相关 pytest 最小集、ruff、`python manage.py check` 通过；`openspec validate "2026-10-08-fix-device-tool-user-id-injection" --strict` 通过。**验证结果**：`apps/` 与前端零改动；54 通过 + 1 跳过；ruff 与格式检查通过；`manage.py check` 无问题；`openspec validate`（含 `--strict`）通过。
