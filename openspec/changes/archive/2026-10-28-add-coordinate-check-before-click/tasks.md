## 1. 坐标核对工具

- [x] 1.1 `engines/agents/tools/tool_img_b64.py`：新增设备向工具 `mark_dot(serial, x, y, normalized=True)`，截屏后在坐标处画红点并返回 `{"image": {base64, media_type}}`；保留 `mark_dot_b64` 纯函数。验证：截屏替身返回 200x100 PNG，归一化 (0.5,0.5) 后 (100,50) 为纯红、其余像素不变；JPEG 进 JPEG 出。**验证结果**：`test_tool_img_b64.py` 9 项全绿；`PlatformFunctionTool` 实测输出 `DataBlock`，日志只记 media_type 与 base64 长度。
- [x] 1.2 失败路径：截屏异常、非法 base64、像素坐标越界均返回 `{"error": ...}`，并写 warning 日志。验证：三类失败各有一条用例断言 error 文案。**验证结果**：`test_bad_capture_returns_error`、`test_bad_base64_returns_error`、`test_bad_pixel_coordinate_returns_error` 全绿。

## 2. 装配与提示词

- [x] 2.1 `engines/agents/tools_config.py`：把 `mark_dot` 放进 `EXECUTOR_BASIC_TOOL_NAMES`，验收角色常驻组保持不变。验证：组装执行工具包后 basic 组为 screenshot_page / mark_dot / press_key；验收包不含 mark_dot。**验证结果**：`build_executor_toolkit()` 实测 basic 为 `['screenshot_page', 'mark_dot', 'press_key']`；`test_assigned_to_executor_basic_only` 断言验收角色与可开关组都不含它。
- [x] 2.2 `engines/agents/prompts/executor_prompt.py`：新增「坐标核对（硬约束）」一条，要求估算坐标与 `xpath_action` 返回坐标都先 `mark_dot(serial, x, y)` 打红点（像素坐标传 `normalized=False`），红点不在目标上重新确定并再次标记，确认前禁止点击；xpath 坐标核对失败时重取 xpath，不按截图重估；工具组说明补「坐标核对」。验证：提示词包含两类坐标来源、`normalized=False`、重算要求与禁止提前点击的表述。**验证结果**：`test_role_prompt_guardrails.py` 8 项全绿（新增 `test_executor_prompt_requires_coordinate_marking_before_click`）。

## 3. 验证

- [x] 3.1 相关用例最小集：`tests/engines/agents/test_tool_img_b64.py` + `tests/graybox/unit/test_role_prompt_guardrails.py`。验证：全绿。**验证结果**：**17 passed**（1.20s）。
- [x] 3.2 静态检查：改动文件 `ruff format --check` 与 `ruff check`。验证：全部通过。**验证结果**：6 files already formatted；All checks passed。
- [x] 3.3 规格校验：`openspec validate add-coordinate-check-before-click --strict`。验证：通过。**验证结果**：见提交流程校验输出。
