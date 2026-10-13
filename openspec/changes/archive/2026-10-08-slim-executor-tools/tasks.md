## 1. 工具子集收敛

- [x] 1.1 `engines/ai/agents/config.py` 的 `VISION_TOOLS` 收敛为 9 个引擎自带设备动作工具（`screenshot_page` / `click_ratio` / `tap_screen` / `xpath_action` / `swipe_screen` / `drag_ratio` / `input_text` / `press_key` / `app_control`），不改其它字段与文件。验证：装配执行模型后，工具子集恰为这 9 个且来源全为 `engines.ai.tools.tool_device`。**验证结果**：生产链路装配后 `executor tools = [screenshot_page, click_ratio, tap_screen, xpath_action, swipe_screen, drag_ratio, input_text, press_key, app_control]`，来源计数 `engine-owned: 9`；文件内除该字段外无其它改动。
- [x] 1.2 同步受影响的既有断言：`tests/graybox/unit/test_device_log_read_tool.py` 中「日志查询工具装配进执行模型」的断言改为「不装配」；`tests/graybox/unit/test_ai_model_debug.py` 与 `tests/graybox/unit/test_ai_platform_tool_debug.py` 中按旧子集的断言改为按新子集计算，其余意图（子集与装配一致、记账工具不进调试对话、拆出的写工具可用）保持不变。验证：相关文件全绿。**验证结果**：共 3 个文件、4 处断言同步；最小集 109 项全绿。

- [x] 1.3 删除执行提示词里的「平台设备操作 SOP」段（保留「行为规范」与「截图铁律」），消除其中对 `list_devices` 的引用。验证：提示词不再含 SOP 标题与该工具名，其余章节不变，相关用例全绿。**验证结果**：`VISION_PROMPT` 章节为 `[角色, 行为规范, 截图铁律, 输入, 输出字段, 输出格式约束, 案例]`；`平台设备操作 SOP` 与 `list_devices` 均零命中；长度 1187 字符；相关用例 80 项全绿，ruff 通过。

## 2. 规格与关单

- [x] 2.1 两份规格 delta：`device-log-read-tool`（删除「工具装配进执行模型」并新增「日志查询工具的装配范围」）、`ai-device-action`（包名查询改为平台侧工具、不装配执行模型）。验证：`openspec validate "2026-10-08-slim-executor-tools" --strict` 通过。**验证结果**：`openspec validate` 与 `--strict` 均通过。
- [x] 2.2 最小集测试与汇报：跑本次触及的测试文件与相邻用例，确认 `apps/` 与前端零改动后汇报。验证：用例全绿、`python manage.py check` 通过、diff 中 `apps/` 与 `frontend/` 零命中。**验证结果**：109 项全绿；`manage.py check` 无问题；ruff 与格式检查通过；`apps/` 零命中，`frontend/` 仅有两处**会话开始前已存在**的改动（属在办的另一单），本单未触碰前端。
