## Why

`check_device_log` 已经能按型号和端口读抓取文件，但起点之后 5 秒内没有可解析行时，一律当成「日志为空」。采集只写了不到 5 秒、文件里根本没有日志、窗口已经盖满但没有关键词，这三种情况现在分不开，验收会把「还没采够」判成断连或未命中。

## What Changes

- `check_device_log` 只读 `logs/serial_logs/{SKU}_{端口}.log` 这一份当前文件。用调用方传入的型号和端口锁定文件，不读其它端口、轮转备份或内存缓冲。
- 从起点（含起点）向后 5 秒，在抓到的原文里匹配关键词，忽略大小写。命中仍返回 logging 时间、该行原文和 `PASS`。
- 三种不满足分开返回：
  - 文件不存在、没有可解析行，或起点之后没有任何行：抛出「日志为空，请检查断后是否正确连接，此轮执行终止」。
  - 起点之后有行，但文件里最晚一行仍早于起点加 5 秒：抛出「从起始点开始日志内容时间不满足5s」。
  - 最晚一行已经到达或超过起点加 5 秒，而这 5 秒内没有该关键词：返回 `FAIL`，说明为「时间段内未抓到关键字」，不抛错。
- **BREAKING**：从 `engines/agents/tools/tool_serial.py` 去掉 `read_device_log`。不再提供按可变跨度翻日志、读内存缓冲、合并同一毫秒、还原功能点，以及「端口未配置 / 端口已关闭」这些结论。
- 缺少关键词、起点、型号或端口时仍返回 `FAIL`，不抛错。关键词仍按原文匹配，不查关键词表做替换。

## 关联文档

无关联需求编号。这条返回口径不在现有需求条目里，来自本次对验收工具的收窄。

## Capabilities

### New Capabilities

### Modified Capabilities

- `device-log-read-tool`：`check_device_log` 改为按「日志为空 / 时间不足 5 秒 / 时间段内未抓到关键字」三种结论区分；文件锁定为 `{SKU}_{端口}.log`。移除 `read_device_log` 的查询、时间点、端口、关键词还原、合并排序、无日志说明和装配范围要求。
- `ai-platform-tool-debug`：调试页里以 `read_device_log` 为样例的参数标签场景改为仍注册的工具。调试页本身的表单和 schema 行为不变。

## Impact

- `engines/agents/tools/tool_serial.py`：只保留 `check_device_log` 及其注册。
- `apps/ai_assistant/tools.py`：去掉 `read_device_log` 的注册、分类和参数中文名。
- 验收提示词里对 `check_device_log` 的失败口径要改成这三种结论。验收角色的工具名单不变，仍然是截图加 `check_device_log`。
- 测试：`tests/graybox/unit/test_device_log_check_tool.py` 覆盖三种结论；`test_device_log_read_tool.py` 里针对 `read_device_log` 的用例随工具删除。`test_tool_debug_param_labels.py` 和 `test_ai_platform_tool_debug.py` 里点名该工具的断言要改到仍存在的工具上。
- 不改 `engines/uart_log` 的监听和落盘，不改端口页查看，不改 `logbus.py` 里的关键词索引和证据窗口。
