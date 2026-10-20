## Context

见 proposal.md - Why。现状是 `engines/device/logbus.py` 用 `_TcpCollector` 按端口监听无线串口盒的 TCP 端口，可选再开一路本机 COM；抓到的行先进内存缓冲，再由 `logfiles.LogFileSink` 写成「北京时间 [来源] 原文」。端口页的开关在 `apps/ai_assistant/log_port_service.py`，经 `LogBus.start_source` / `stop_source` 生效。`utils/logs.py` 的 `build_logger` 已规定行格式、10MB 与 3 个备份，但按记录器名称去重：同名且已有 handler 时直接返回，不会改绑文件。

## Goals / Non-Goals

**Goals:**

- 采集只留在 `engines/uart_log`，对外只有检测、接收、写入、开关。
- 写入走 `utils/logs.py`，不新写一套格式和轮转。
- 端口页的开关改调这套开关，第 11 路拒绝。
- 日志查看改为展示 logging 记录里的消息正文。

**Non-Goals:**

- 不重写关键词、开窗、等级判定和 `read_device_log` 的解析。
- 不打开本机 COM。
- 不把波特率送进检测或接收。

## Decisions

### 1. 四个类，外加一份参数

| 类 | 模块 | 职责 |
|---|---|---|
| `PortParams` | `engines/uart_log/params.py` | 监听地址、端口、SKU、单行上限（默认 4096）、重连间隔。不含波特率 |
| `PortDetector` | `engines/uart_log/detect.py` | 绑定前探测端口是否已被占用；失败时记可读错误并返回未监听 |
| `PortReceiver` | `engines/uart_log/receiver.py` | 一个端口一条线程：绑定、多连接、按行切开、断线后继续听。检测不通过则不进入监听集合 |
| `CaptureWriter` | `engines/uart_log/writer.py` | 把一行原文交给该端口的记录器 |
| `PortSwitch` | `engines/uart_log/switch.py` | 按端口启停，持有接收线程；同时监听数不超过 10 |

备选是继续把线程留在 `LogBus` 里只改落盘。那样设备控制与采集仍在同一个文件，和「挪到 `engines/uart_log`」不符。

`PortSwitch` 是进程内单例，由端口编排在启动和改开关时调用。重复打开同一端口直接返回已有线程。关闭时关掉监听套接字并等待线程结束，从而释放端口。

### 2. 写入复用 `build_logger`，记录器按端口分开

`utils/logs.py` 增加按 SKU 与端口取得记录器的函数。名称 `uart.{SKU}.{端口}`，路径 `logs/serial_logs/{SKU}_{端口}.log`。SKU 写入文件名前去掉路径字符。等级用 INFO：文件收得到，控制台仍只出 WARNING，避免抓取内容刷屏。

`serial_log` 仍写 `logs/serial.log`，只收监测代码自己的错误。抓到的原文不写进 `serial_log`。

备选是让 `CaptureWriter` 自己 `open()` 追加。那样会再做一份轮转，和「格式与轮转都不动」冲突。

### 3. 旧缓冲和旧行写入留在原模块，但不再被采集调用

`KeywordIndex`、开窗、`build_evidence`、`now_stamp`、旧行解析仍留在 `engines/device/logbus.py` 与 `logfiles.py`。采集线程、本机 COM、`LogFileSink` 的写入、以及采集对内存缓冲的灌入从运行路径去掉。证据窗口不再收到新行，与 `device-log-evidence` 的变更一致。

备选是删掉整个 `logbus.py`。关键词和验收的 import 会断，本次就要改判定代码，超出范围。

### 4. 端口页只换采集入口和读文件方式

`log_port_service` 的开关改调 `PortSwitch`。手动打开第 11 路时不把库中的开关写成打开，接口返回可读结论。进程启动时若库里打开的端口超过 10 个，按端口号只恢复前 10 个，其余保持原开关值但不监听，并写一条代码日志。

日志查看不再用 `parse_log_line` 的「北京时间 [来源] 原文」，也不再按同一毫秒合并。它读取 `logs/serial_logs/{SKU}_{端口}.log` 的尾部，展示 logging 行的时间与消息。`read_device_log` 仍走旧解析，因此对新文件得到「该时间范围内无日志」。

文件大小展示改为该新路径。列表接口的字段名、信封和开关权限不变。

## 模块防火墙自检

- 跨 App import：不新增。`apps/ai_assistant` 只增加对 `engines.uart_log` 的导入，方向仍是 App → 引擎。
- 不 import 其它 App 的 service、runner、consumer。
- 开关的持久化仍走 `apps/ai_assistant/api.py` 已有的写库函数，不在引擎里写库。
- 前端不直连数据库，仪表盘无写操作。
- `engines/uart_log` 不 import `django` 或 `apps`。套接字只出现在 `receiver.py`。

## Risks / Trade-offs

- [验收与 `read_device_log` 读不到新行] → 本次按确认口径接受。证据窗口固定返回「窗口内无日志」。旧解析保留，避免半改判定。
- [未归档的 `unified-utils-logs` 禁止按 SKU 改选文件，并要求采集原文保持旧格式] → 以本次口径为准。实施时不要把抓取记录器并进那个变更的「四个固定记录器」。
- [`build_logger` 同名即复用 handler] → 记录器名必须带 SKU 和端口。实施时用临时目录断言两个端口不会写进同一文件。
- [第 11 路在启动恢复与手动打开上的库状态不同] → 手动打开失败则不改库；启动只限制实际监听数。两种都要有单测。
- [Windows 上关套接字才能立刻释放端口] → 关闭时先关监听套接字，再等线程结束。沿用现有 0.5 秒 accept 超时。

## Migration Plan

1. 先加 `engines/uart_log` 与 `utils/logs.py` 的按端口记录器，用本地套接字单测收行和落盘。
2. 端口编排改调 `PortSwitch`，日志查看改读新文件。
3. 从 `logbus.py` 去掉 TCP / COM 采集和对缓冲的灌入，去掉 `LogFileSink` 的写入调用。
4. 回滚时恢复端口编排对 `LogBus.start_source` 的调用即可回到旧监听；已写入 `logs/serial_logs/` 的文件可留在磁盘，不参与回滚。
