## Why

串口日志现在同时走监听写文件、内存缓冲开窗、旧行格式解析和调试台历史取证。抓取文件已经是 logging 行，查关键字也只读这一份文件。其余串口路径不再被使用，还各自认一套时间。

## What Changes

留下四件事：

- `engines/uart_log` 继续负责监听和写入。端口开关仍是打开或关闭这次监听的入口，波特率仍只展示、不参与监听。
- `engines/agents/tools/tool_serial.py` 的 `check_device_log` 继续按型号和端口锁定 `logs/serial_logs/{SKU}_{端口}.log`，用设备动作返回的时间点作为起点，在其后 5 秒的原文里匹配关键字。三种结论不变：日志为空、从起始点开始未满 5 秒、时间段内未抓到关键字。
- `apps/ai_assistant` 读取该本地文件，按文件顺序把原文行显示在平台上。不再把行拆成时间戳和正文，也不再按时间倒序。
- 设备控制工具（`engines/agents/tools/tool_device.py`，以及仍返回 `action_time` 的 `engines/ai/tools/tool_device.py`）用 `time` 取本地当前时间，格式与 logging 的 `asctime` 一致：`YYYY-MM-DD HH:MM:SS,mmm`（例如 `2026-10-19 11:06:14,909`）。只读动作不返回该时间。

**BREAKING**：除此以外的串口功能全部去掉。

- 去掉证据开窗、关窗读缓冲、`build_evidence`，以及工作流为串口注入的日志证据。
- 去掉调试台按旧文件做的历史取证。
- 去掉 `时间戳 [来源] 原文` 的写入、解析和按时间范围读取，以及按日期改名的 50MB 轮转。
- 去掉内存缓冲里的串口行、北京时间 `now_stamp()`，以及执行步骤里「附带 5 秒窗口日志和命中等级」这一块。点击时间点和点击后截图仍留下，时间格式改为上面的 logging 格式。
- 关键词表仍只给验收模型挑选 `check_device_log` 的 keyword，不参与监听、写文件或按行解析。

未实施的 `drop-old-log-line-time` 被本变更取代，不按那一单改代码。

## 关联文档

无关联需求编号。这是把串口日志收成监听写入、按动作时间查关键字、平台显示文件这三条，并删掉其余串口路径。

## Capabilities

### New Capabilities

### Modified Capabilities

- `device-log-port-console`：日志查看改为按文件顺序展示原文行。端口列表和监听开关保留。采集与落盘格式不在本变更重复规定，沿用未归档的 `uart-log-monitor`。
- `device-log-read-tool`：`check_device_log` 的起点时间与 logging 的逗号毫秒格式一致，来源是设备动作返回的 `action_time`。
- `device-log-evidence`：去掉开窗、按北京时间切缓冲和把窗口日志交给验收模型。验收查日志只走 `check_device_log`。
- `ai-executor-log-check`：去掉步骤上附带的 5 秒窗口日志与命中等级。点击证据仍保留时间点和截图，时间改为 logging 格式。
- `ai-device-action`：副作用动作的发出时间改为 `time` 取得的本地时间，格式为 `YYYY-MM-DD HH:MM:SS,mmm`。

## Impact

- `engines/uart_log`：不改监听、写入、10 路上限和 logging 落盘。
- `engines/agents/tools/tool_serial.py`：起点按 logging 时间格式解析。
- `engines/agents/tools/tool_device.py`、`engines/ai/tools/tool_device.py`：`action_time` 改用 `time`，不再调用 `now_stamp()`。
- `apps/ai_assistant/log_port_service.py`：查看日志改为读当前抓取文件的原文行。
- `apps/ai_assistant/log_evidence.py`、`apps/ai_assistant/log_history.py`：去掉开窗和历史取证。`engines/device/logbus.py`、`engines/device/logfiles.py` 里只为这些串口路径服务的缓冲、开窗、旧行格式和北京时间戳一并删除。
- 工作流里为串口证据调用 `open_window` / `read_window` 的接线去掉。验收提示词里的查日志步骤仍使用 `check_device_log`，`at` 抄 `action_time`。
- 前端端口查看改为显示原文行。步骤上的窗口日志块去掉；点击时间和截图的展示留下，时间字符串改为新格式。
- 测试：端口查看、设备动作时间、`check_device_log`、证据开窗和历史取证相关用例随行为改或删。不跑全量回归。
