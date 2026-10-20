## Why

设备端口日志的监听、缓冲、落盘、关键词和取证堆在 `engines/device/logbus.py` 里，和设备控制混在一起。采集层需要单独收成「检测、接收、写入、开关」，并且最多同时监听 10 个端口。

## What Changes

- 新增 `engines/uart_log`，只做四件事：检测端口能否监听、按行接收串口日志、把抓到的内容写入文件、按端口开关。参数（监听地址、端口、SKU、行长上限、重连间隔）从监测逻辑里抽出来。
- 同时处于监听中的端口最多 10 个。第 11 个端口的开启请求必须拒绝，已打开的端口不受影响。
- 只监听已登记的 TCP 端口（无线串口盒推日志的端口）。不打开本机 COM。
- 每个端口一个记录器，名称 `uart.{SKU}.{端口}`。文件为 `logs/serial_logs/{SKU}_{端口}.log`。写入经 `utils/logs.py` 现有格式 `%(asctime)s - %(name)s - %(levelname)s - %(message)s`。消息正文只放抓到的那一行，不加「北京时间 [来源] 原文」。时间用 logging 的时间。轮转沿用该模块现有规则：单文件 10MB，保留 3 个备份。
- **BREAKING**：采集层不再维护内存环形缓冲，不再生成 `YYYY-MM-DD HH:MM:SS.mmm [来源] 原文` 行，不再按 50MB 改名为 `{SKU}_{端口}_{日期}.log`。
- **BREAKING**：关键词、开窗、取证、按时间回读的入口本次不重写。采集不再往内存缓冲灌行，新文件也不再是旧行格式，因此这些入口不能再按原口径从新日志里取出行。
- `engines/device/logbus.py` 中的监听与 `engines/device/logfiles.py` 中的采集原文写入迁出后删除。`engines/device` 只保留设备控制。

## 关联文档

无关联需求编号。本次只把设备端口日志的采集层从设备控制里拆出去，不新增产品功能入口。

## Capabilities

### New Capabilities

- `uart-log-monitor`: 端口检测、按行接收、经 `utils/logs.py` 写入 `logs/serial_logs/{SKU}_{端口}.log`、开关，以及同时最多 10 个端口。

### Modified Capabilities

- `device-log-capture`: 常驻采集改为上述四功能；去掉内存缓冲、北京时间毫秒行、本机 COM 来源；同时监听数有上限。
- `device-log-file-archive`: 目录改为 `logs/serial_logs/`，行格式改为 logging 格式，轮转改为 10MB 与 3 个备份。
- `device-log-port-console`: 打开第 11 个端口时必须拒绝；日志查看读到的是 logging 行，不再按「北京时间 + 来源」合并。
- `device-log-evidence`: 采集不再提供内存缓冲行，开窗与等级判定入口保留，但不保证从新日志按原时间窗取到行。
- `device-log-read-tool`: 查询数据源不再包含采集内存缓冲；按旧行格式解析新文件时得不到新行。

## Impact

- 代码：新增 `engines/uart_log/`；`utils/logs.py` 增加按 SKU 与端口取得记录器的入口；删除 `engines/device/logbus.py`、`engines/device/logfiles.py` 中的采集与原文归档实现。调用方包括 `apps/ai_assistant/log_port_service.py`、`log_evidence.py`、`log_history.py`、`log_keywords.py`，以及 `engines/agents/tools/tool_serial.py`、`engines/agents/tools/tool_device.py`、`engines/ai/tools/tool_device.py`。
- 测试：`tests/graybox/unit/test_device_log_bus.py`、`test_device_log_files.py`、`test_device_log_file_range.py`、`test_log_port_service.py`、`test_log_ports_api.py`、`test_device_log_evidence.py`、`test_device_log_read_tool.py`、`test_ai_log_evidence_wiring.py`、`test_ai_log_keywords.py`。
- 未归档变更 `unified-utils-logs` 要求采集原文保持「北京时间 [来源] 原文」，且串口代码日志不得写入 `{SKU}_{端口}.log`。本变更与之冲突：抓到的串口内容写入 `logs/serial_logs/{SKU}_{端口}.log`，并使用 logging 行格式。以本次确认的口径为准。
- 不改端口页的开关权限、列表接口和信封。不改关键词目录与验收等级的判定代码。
