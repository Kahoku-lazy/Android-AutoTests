## Context

见 proposal.md 的 Why。`check_device_log` 已用 `capture_file_path` 读 `logs/serial_logs/{SKU}_{端口}.log`，并用 logging 行正则取出抓到的原文。起点之后 5 秒内没有行时，它抛出同一句「日志为空」。`read_device_log` 仍在同一文件里，经内存缓冲和旧行解析返回合并列表，并在函数内部引用 `apps.ai_assistant.log_port_service`。

## Goals / Non-Goals

**Goals:**

- 用全文件里起点之后的最晚一行，区分「日志为空」「时间不足 5 秒」「窗口已盖满但没有关键词」。
- 删掉 `read_device_log` 后，引擎工具不再引用 `apps`。

**Non-Goals:**

- 不改 `engines/uart_log` 的监听、写入和 10 路上限。
- 不改端口页查看，不改 `logbus.py` 的关键词索引和证据窗口。
- 不把三种结论收成同一种返回值。

## Decisions

1. 盖满与否看起点之后的最晚一行，关键词只在窗口内找。先解析当前文件的全部 logging 行。没有 `epoch >= 起点` 的行，判日志为空。有这样的行且最晚一行仍早于起点加 5 秒，判时间不足。最晚一行到达或超过起点加 5 秒时，只在 `[起点, 起点+5秒]` 内的原文里做忽略大小写的子串匹配。窗口之后的行可以证明时间已经盖满，但不参与匹配。备选是「窗口内没有任何行就当日志为空」。那样采到了 6 秒、但关键词落在第 6 秒之外时，仍会和断连混在一起，与已确认口径不符。

2. 前两种中断用 `ValueError`，未命中用现有 JSON。日志为空沿用 `LOG_EMPTY`。时间不足抛出「从起始点开始日志内容时间不满足5s」。未命中返回 `result=FAIL`，`msg` 为「时间段内未抓到关键字」。缺少关键词、起点、型号或端口时仍返回 `result=FAIL` 且 `msg` 为空，避免和未命中混成一句。命中仍是 `timestamp`、`msg`、`result=PASS`。备选是三种都抛错。未命中抛错会被当成工具失败，验收模型无法把它当成「查过了，没有」的结论。

3. 文件只通过 `utils.logs.capture_file_path` 定位。不读轮转备份，不读 `DEVICE_LOG_LOG_DIR` 下的旧格式文件，不调用 `get_log_bus`。型号字符与写入侧的 `safe_sku` 一致。

4. `read_device_log` 从 `tool_serial.py` 和 `apps/ai_assistant/tools.py` 的注册、分类、参数中文名里删除。调试页样例改到 `check_device_log` 已有的中文名：关键词「要检查的日志关键词」、起点「取证起点时间」、型号「设备型号」。验收提示词里「5 秒内有日志但没有关键词则 FAIL」改成这三种结论。执行技能手册里对 `read_device_log` 的说明一并删掉，避免模型去调一个已经不存在的工具。

## 模块防火墙自检

- 不新增跨 App import。删掉 `read_device_log` 后，`tool_serial.py` 不再在函数内引用 `apps.ai_assistant.log_port_service`。
- 不写库，不新增 ORM。
- 前端不直连数据库。本变更不改页面结构，调试页只是样例工具从 `read_device_log` 换成 `check_device_log`。
- `engines/uart_log` 继续不依赖 `django` 或 `apps`。

## Risks / Trade-offs

- [未归档的 `uart-log-monitor` 仍在修改 `read_device_log` 的需求] → 本变更按需求名移除这些需求。归档时先归档 `uart-log-monitor`，再归档本变更；若顺序反过来，归档 `uart-log-monitor` 时那些 MODIFIED 会失去落点，需要先从它的 delta 里拿掉已被本变更取代的 `read_device_log` 段落。
- [窗口之后才出现的关键词会被判成未命中] → 这是 5 秒窗口的既有边界。后到的行只用来证明时间已经盖满。
- [调试页不再能按任意跨度翻日志] → 看原文改走端口页的抓取文件。本变更不补一个新的翻阅工具。

## Migration Plan

1. 先改 `check_device_log` 的三种结论，再删 `read_device_log` 及其注册，避免中间状态里检查口径还没分开、查询工具已经没了。
2. 回滚时恢复 `tool_serial.py` 与 `apps/ai_assistant/tools.py` 的注册即可。已写好的 `logs/serial_logs/` 文件不参与回滚。
