## 1. 动作时间与检查起点

- [x] 1.1 在 `utils/logs.py` 增加用 `time` 取得本地当前时间的函数，格式为 `YYYY-MM-DD HH:MM:SS,mmm`。`engines/agents/tools/tool_device.py` 与 `engines/ai/tools/tool_device.py` 的副作用动作改用它写入 `action_time`，不再调用 `now_stamp()`。只读动作仍不返回该字段。验证：`python -m pytest tests/graybox/unit/test_ai_log_evidence_wiring.py tests/graybox/unit/test_device_log_check_tool.py -q` 通过，且两处设备工具的副作用返回里能看到逗号毫秒。

- [x] 1.2 `check_device_log` 的起点接受 `YYYY-MM-DD HH:MM:SS,mmm`，并与文件行的 logging 时间比较。只到秒按该秒的 `,000`，只给时刻按本地当天。三种结论文案不变。验收提示词写明 `at` 抄该发出时刻。验证：`python -m pytest tests/graybox/unit/test_device_log_check_tool.py -q` 通过，且用 `2026-10-19 11:06:14,909` 这种起点能命中。

## 2. 平台按文件顺序显示原文

- [x] 2.1 `apps/ai_assistant/log_port_service.py` 的日志查看按文件顺序返回当前文件尾部的原文行，不拆时间戳和正文，不倒序。关闭监听仍返回「端口已关闭监听」且不读文件。前端日志窗口按该顺序显示整行。验证：`python -m pytest tests/graybox/unit/test_log_port_service.py tests/graybox/unit/test_log_ports_api.py -q` 通过。

## 3. 去掉其余串口路径

- [x] 3.1 工作流不再为串口调用 `open_window` / `read_window`。步骤上的日志检查块只保留点击时间点和截图路径，不再附带窗口日志或命中等级。删除 `apps/ai_assistant/log_evidence.py` 的开窗、`apps/ai_assistant/log_history.py` 的历史取证，以及 `engines/device/logbus.py`、`engines/device/logfiles.py` 里的缓冲、开窗、旧行格式和北京时间戳。关键词索引和关键词文件留下。验证：`python -m pytest tests/graybox/unit/test_ai_workflow_log_evidence.py tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_device_log_evidence.py tests/graybox/unit/test_ai_debug_log_history.py -q` 通过；已删除行为对应的测试文件改掉或去掉，不再引用已删除的函数。

## 4. 收口

- [x] 4.1 对改过的路径跑 `ruff check` 与 `ruff format --check`。验证：这两条命令退出码为 0。
- [x] 4.2 跑边界检查。验证：`python tools/gen_arch_stats.py --check-boundaries` 通过。
