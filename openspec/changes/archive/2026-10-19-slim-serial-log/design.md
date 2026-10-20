## Context

见 proposal.md 的 Why。监听和写入已在 `engines/uart_log`，当前文件是 logging 行。`check_device_log` 已按型号和端口读该文件并做 5 秒关键词判断，但起点解析认的是点号毫秒。设备动作的 `action_time` 仍由 `now_stamp()` 写成北京时间点号毫秒。端口页把 logging 行拆成时间戳和正文后倒序展示。证据开窗、调试台历史取证和旧行格式解析仍留在 `logbus.py`、`logfiles.py`、`log_evidence.py` 和 `log_history.py`。

## Goals / Non-Goals

**Goals:**

- 副作用动作的发出时间与 logging 的 `asctime` 使用同一种本地时间字符串。
- 检查工具用这个时间做起点。
- 端口页按文件顺序显示原文行。
- 去掉开窗、历史取证、内存缓冲和旧行格式。

**Non-Goals:**

- 不改 `engines/uart_log` 的监听、写入、10 路上限和 10MB 备份。
- 不移动关键词表文件，不改词条内容。
- 不改点击后截图的采集和路径。
- 不实施 `drop-old-log-line-time`。

## Decisions

1. 发出时间用 `time.time()` 取本地时间，格式为 `YYYY-MM-DD HH:MM:SS,mmm`。两处设备工具（`engines/agents/tools/tool_device.py` 与 `engines/ai/tools/tool_device.py`）调用同一函数，放在 `utils/logs.py`，与 logging 的时间格式放在一处。只读动作仍不返回 `action_time`。备选是继续用 `now_stamp()` 再把点号换成逗号。那仍会按北京时间换算，和 logging 使用的本地时间不是同一套钟。

2. `check_device_log` 的起点增加对逗号毫秒的解析，并与文件行的 logging 时间用同一套比较。只到秒仍按该秒的 `,000`。只给时刻时日期取本地当天。三种结论的文案不变。

3. 端口查看读取当前文件尾部，按文件顺序返回原文行，字段只保留整行文本。前端不再拆时钟和正文，也不再倒序。关闭监听时查看仍返回「端口已关闭监听」，不读文件。

4. 删除证据开窗、关窗读缓冲、`build_evidence`、调试台历史取证，以及 `时间戳 [来源] 原文` 的写入、解析和按范围读取。工作流不再调用 `open_window` / `read_window`。步骤上的日志检查块只保留点击时间点和截图路径。关键词索引和关键词文件留下，继续给验收提示词选词。`logbus.py`、`logfiles.py` 在没有剩余调用方后删除；关键词索引若是其中唯一留下的部分，迁到 `engines/device/keywords.py`。

5. 验收提示词写明 `at` 抄 `action_time`，格式为逗号毫秒。

## 模块防火墙自检

- 不新增跨 App import。`apps/ai_assistant` 少引用 `log_evidence` 的开窗和 `log_history` 的历史取证。
- 不写库，不新增 ORM。端口开关仍只经 `apps/ai_assistant/api.py` 写开关状态。
- 前端只改日志查看的展示数据，不直连数据库。
- `engines/uart_log` 不依赖 `django` 或 `apps`。

## Risks / Trade-offs

- [未归档的 `uart-log-monitor` 与 `check-device-log-capture-file` 也在改采集、落盘和检查工具] → 归档时先归档这两单，再归档本变更。本变更不重复写采集和落盘的 delta。若先归档的变更已经删掉同名需求，归档本变更前从 delta 里拿掉已经不存在的段落。
- [步骤记录不再附带窗口日志] → 核对关键词改由验收模型调用 `check_device_log`。点击时间和截图仍在步骤记录里。
- [机器本地时区与北京时间不一致时，发出时间不再强制换成 UTC+8] → 这是为了和 logging 的 `asctime` 用同一套钟。部署机器应使用同一本地时区。

## Migration Plan

1. 先改发出时间和检查工具的起点解析，再改端口页展示，最后删除开窗、历史取证和旧行格式。避免检查工具还在要点号时间、动作已经只返回逗号时间。
2. 回滚时恢复 `now_stamp()` 与开窗调用。已经写成 logging 格式的 `logs/serial_logs/` 不参与回滚。
