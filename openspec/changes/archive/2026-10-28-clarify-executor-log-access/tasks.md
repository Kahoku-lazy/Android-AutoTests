## 1. 提示词约束

- [x] 1.1 `engines/agents/prompts/executor_prompt.py`：新增第 14 条——设备串口日志检查由验收模型通过日志工具完成，只有验收模型有该权限；执行模型禁止尝试检查、推测或声称检查过日志，也不在 handover 里写日志结论；只需给出 `action_time` 供验收模型核对。验证：提示词包含上述四类表述。**验证结果**：`test_role_prompt_guardrails.py` 新增 `test_executor_prompt_declares_log_check_belongs_to_verifier`，断言四条文案齐全。

## 2. 验证

- [x] 2.1 相关用例最小集：`tests/graybox/unit/test_role_prompt_guardrails.py` + `tests/engines/agents/test_tool_img_b64.py`。验证：全绿。**验证结果**：**18 passed**。
- [x] 2.2 静态检查：改动文件 `ruff format --check` 与 `ruff check`。验证：全部通过。**验证结果**：2 files already formatted；All checks passed。
- [x] 2.3 规格校验：`openspec validate clarify-executor-log-access --strict`。验证：通过。**验证结果**：通过。
