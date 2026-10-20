## 1. 按端口取得记录器

- [x] 1.1 在 `utils/logs.py` 增加按 SKU 与端口取得记录器的函数：名称 `uart.{SKU}.{端口}`，文件 `logs/serial_logs/{SKU}_{端口}.log`，复用现有 `build_logger` 的格式、10MB 与 3 个备份。SKU 中的路径字符去掉。验证：`python -m pytest tests/graybox/unit/test_uart_log.py -q -k recorder` 通过，且两个端口的记录不会出现在同一个文件里。

## 2. 采集四类

- [x] 2.1 新增 `engines/uart_log/params.py` 的 `PortParams`（监听地址、端口、SKU、单行上限默认 4096、重连间隔，不含波特率）和 `detect.py` 的 `PortDetector`。端口已被占用或绑定失败时记录可读错误，且不把该端口标成正在监听。验证：`python -m pytest tests/graybox/unit/test_uart_log.py -q -k detect` 通过。
- [x] 2.2 新增 `receiver.py` 的 `PortReceiver`：一个端口一条线程，多连接，按行切开，空行不收，超长行截断后续写，连接断开后仍监听。验证：`python -m pytest tests/graybox/unit/test_uart_log.py -q -k receive` 通过（用本地套接字推入多行，不连真机）。
- [x] 2.3 新增 `writer.py` 的 `CaptureWriter`：消息只含抓到的原文，等级 INFO，写失败不中断接收。验证：`python -m pytest tests/graybox/unit/test_uart_log.py -q -k write` 通过，文件中该行匹配 `时间 - uart.{SKU}.{端口} - INFO - 原文`。
- [x] 2.4 新增 `switch.py` 的 `PortSwitch`：按端口打开和关闭，重复打开不产生第二份监听，关闭后释放端口，同时监听超过 10 个时拒绝新的一路且已打开的端口不变。验证：`python -m pytest tests/graybox/unit/test_uart_log.py -q -k switch` 通过。

## 3. 端口页改接新开关

- [x] 3.1 `apps/ai_assistant/log_port_service.py` 的开关与启动恢复改调 `PortSwitch`。手动打开第 11 路时不把库中的开关写成打开，并返回可读结论。启动时若已打开的端口超过 10 个，只按端口号恢复前 10 个，其余不监听并写代码日志。写库仍走 `api.py`。验证：`python -m pytest tests/graybox/unit/test_log_port_service.py tests/graybox/unit/test_log_ports_api.py -q` 通过。
- [x] 3.2 日志查看改为读取 `logs/serial_logs/{SKU}_{端口}.log` 的尾部，展示 logging 行的时间与消息，不再按「北京时间 + 来源」合并。列表里的文件名和大小改为该路径。验证：`python -m pytest tests/graybox/unit/test_log_port_service.py -q -k read` 通过，窗口能看到抓到的原文。

## 4. 拆掉旧采集路径

- [x] 4.1 从 `engines/device/logbus.py` 去掉 TCP 监听、本机 COM、以及采集对内存缓冲的灌入。`KeywordIndex`、开窗、`build_evidence`、`now_stamp` 保留，现有 import 不改判定逻辑。验证：`python -m pytest tests/graybox/unit/test_device_log_evidence.py tests/graybox/unit/test_ai_log_keywords.py tests/graybox/unit/test_device_log_read_tool.py -q` 通过；其中读新 logging 文件的用例得到「该时间范围内无日志」且不抛错。
- [x] 4.2 去掉 `engines/device/logfiles.py` 里 `LogFileSink` 的写入职责，保留旧行解析供 `read_device_log` 使用。确认运行路径不再把抓取内容写成「北京时间 [来源] 原文」。验证：`python -m pytest tests/graybox/unit/test_device_log_files.py tests/graybox/unit/test_device_log_file_range.py -q` 通过，且仓库内采集写入不再调用 `LogFileSink.write`。

## 5. 收口

- [x] 5.1 对本次改过的路径跑 `ruff check` 与 `ruff format --check`。验证：这两条命令退出码为 0。
- [x] 5.2 跑边界检查，确认没有新增跨 App 内部 import，且 `engines/uart_log` 不依赖 `django` 或 `apps`。验证：`python tools/gen_arch_stats.py --check-boundaries` 通过。
