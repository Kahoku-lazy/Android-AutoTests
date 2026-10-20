## 1. 分开三种检查结论

- [x] 1.1 `check_device_log` 只读 `capture_file_path` 指向的当前文件。没有起点之后的可解析行时抛出「日志为空，请检查断后是否正确连接，此轮执行终止」。起点之后有行但最晚一行早于起点加 5 秒时抛出「从起始点开始日志内容时间不满足5s」。最晚一行已到达或超过起点加 5 秒且窗口内没有关键词时，返回 `result` 为 `FAIL`、`msg` 为「时间段内未抓到关键字」。命中、缺参、只到秒、不替换功能点中文、不匹配记录器名保持现有行为。验证：`python -m pytest tests/graybox/unit/test_device_log_check_tool.py -q` 通过，且其中有这三种结论的用例。

## 2. 去掉通用查询

- [x] 2.1 从 `engines/agents/tools/tool_serial.py` 删除 `read_device_log`，注册列表只留 `check_device_log`。从 `apps/ai_assistant/tools.py` 删除该工具的导入、注册、分类和参数中文名。验收提示词改成这三种结论。执行技能手册不再引导调用 `read_device_log`。验证：`python -m pytest tests/graybox/unit/test_device_log_check_tool.py tests/graybox/unit/test_ai_platform_tool_debug.py tests/graybox/unit/test_tool_debug_param_labels.py -q` 通过，且仓库内不再有可调用的 `read_device_log`。
- [x] 2.2 删除 `tests/graybox/unit/test_device_log_read_tool.py` 里只覆盖 `read_device_log` 的用例。验收工具名单若仍在该文件，改到不依赖已删函数的测试里。验证：`python -m pytest tests/graybox/unit/test_device_log_read_tool.py tests/graybox/unit/test_device_log_check_tool.py -q` 通过；若该文件已删除，则只跑后者。

## 3. 收口

- [x] 3.1 对改过的路径跑 `ruff check` 与 `ruff format --check`。验证：这两条命令退出码为 0。
- [x] 3.2 跑边界检查，确认 `tool_serial.py` 不再引用 `apps`。验证：`python tools/gen_arch_stats.py --check-boundaries` 通过。
