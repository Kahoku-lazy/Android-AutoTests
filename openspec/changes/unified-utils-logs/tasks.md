## 1. 算法包改名为 utils

- [x] 1.1 将 `algorithms` 整包改名为 `utils`，包内相对模块保持不变，并更新 `apps/device_inspector`、`utils` 内部以及测试里的导入。验证：`python -m pytest tests/graybox/unit/test_element_layers.py tests/graybox/unit/test_engine_hierarchy_contract.py -q` 通过，且仓库内不再有 `from algorithms` / `import algorithms`。
- [x] 1.2 收紧引擎边界：引擎可以导入 `utils.logs`，不得导入 `utils` 的算法模块；`engines/device/base.py` 的边界说明与 `test_engine_hierarchy_contract.py` 改为检查 `utils.xpath`、`utils.hierarchy`、`utils.element_layers`、`utils.vision`。验证：同一条层级契约测试通过。

## 2. 全局日志对象

- [x] 2.1 新增 `tests/graybox/unit/test_project_log.py`，覆盖：同一对象、总开关关闭后不创建文件、四组路径互斥、普通行含上海时间毫秒与文件类名等级、模型行含角色模型动作并写入 `logs/agents/agent_events.log`、串口行含地址设备串口号并写入 `logs/serial_logs/H6810_7005.log`、缺 SKU 或端口时写入 `unknown_0.log`、采集目录中的同名文件不被改写、两条日志保持调用顺序、写目录失败不向调用方抛异常。验证：在实现 `ProjectLog` 之前，`python -m pytest tests/graybox/unit/test_project_log.py -q` 失败。
- [x] 2.2 在 `utils/logs.py` 实现 `ProjectLog`，模块底部实例化 `log`。一把锁串行写四组文件；选文件规则、行格式、空字段 `-`、`enabled` 开关与吞掉 `OSError` 按 design.md 的决策 2。该模块不导入 Django 或 `apps`。验证：`python -m pytest tests/graybox/unit/test_project_log.py -q` 通过，且 `python -m ruff check utils/logs.py tests/graybox/unit/test_project_log.py` 通过。

## 3. 智能体与过程日志改走同一实例

- [x] 3.1 改写 `tests/graybox/unit/test_agent_events_show.py` 与 `tests/graybox/unit/test_agent_process_log.py`：事件时间线与过程记录都断言 `logs/agents/agent_events.log`；过程记录不再出现按天文件名；行内仍能看到角色、模型、任务与步骤、事件类型；九个事件动作的措辞保持；标准输出不出现这些行。验证：在改写入方之前，这两条 pytest 失败。
- [x] 3.2 `engines/agents/event_log.py` 的 `write_line` 改为调用 `utils.logs.log`，去掉 loguru。`engines/ai/process_log.py` 的写入改为调用同一个 `log`，保留截断与「独立运行」标识，不再派生 `agents-YYYYMMDD.log`。`engines/agents` 里已有 `__init__` 的运行期类赋 `self.log = log`。验证：`python -m pytest tests/graybox/unit/test_agent_events_show.py tests/graybox/unit/test_agent_process_log.py tests/graybox/unit/test_project_log.py -q` 通过。

## 4. 设备与串口代码日志

- [x] 4.1 `AndroidConnection` 的连接回调改名为 `trace`（参数与 `self.trace`）。连接过程日志改走 `self.log`，并带上地址与串口号。`engines/device` 中已有 `__init__` 的运行期类赋 `self.log = log`。`logbus.py`、`logfiles.py` 里现有的代码日志改经 `self.log` 或模块级 `log`，带上 SKU、端口、地址与设备；`LogFileSink` 仍按原目录与「北京时间 [来源] 原文」写采集原文。验证：`python -m pytest tests/graybox/unit/test_device_log_files.py tests/graybox/unit/test_device_log_bus.py tests/graybox/unit/test_project_log.py -q` 通过，且 `android_device.py` 中不再把回调放在 `self.log`。

## 5. 后端代码日志收口

- [x] 5.1 `apps/` 中已有 `__init__` 的运行期类（不含迁移、不含 Django 模型）赋 `self.log = log`。现有 `logging.getLogger` 的业务日志改为 `self.log` 或模块级 `log`。`model_test` 不再写 `AI-MODEL-TEST.log`。验证：`python -m ruff check apps config/settings.py` 通过，且 `apps/` 与 `config/` 中不再出现指向 `django.log` 或 `AI-MODEL-TEST.log` 的 `FileHandler`。
- [x] 5.2 `config/settings.py` 去掉 `logs/django.log` 的 file handler，控制台 handler 与 `LOG_LEVEL` 保留。更新 `tests/graybox/unit/test_logging_config.py`，断言本地档位不再配置该文件。验证：`python -m pytest tests/graybox/unit/test_logging_config.py tests/graybox/unit/test_project_log.py -q` 通过。

## 6. 收口检查

- [x] 6.1 对本次改动的 Python 文件做静态检查，并重跑本变更点名的单元测试。验证：`python -m ruff check utils engines/agents/event_log.py engines/ai/process_log.py engines/device apps/device_inspector config/settings.py tests/graybox/unit/test_project_log.py tests/graybox/unit/test_agent_events_show.py tests/graybox/unit/test_agent_process_log.py tests/graybox/unit/test_logging_config.py tests/graybox/unit/test_engine_hierarchy_contract.py` 通过，且第 1 至第 5 组点名的 pytest 一并通过。不跑全量回归。

## 7. 日志改成配置类与具名实例

- [x] 7.1 `utils/logs.py` 改为 `LogConfig` + `FileLogger`（标准库 `logging`）与 `SerialLogger`，模块底部实例化 `backend_log`、`agent_event_log`、`device_log`、`serial_log`。控制台默认关闭。调用方改为使用对应实例。验证：`python -m pytest tests/graybox/unit/test_project_log.py tests/graybox/unit/test_agent_events_show.py tests/graybox/unit/test_agent_process_log.py tests/graybox/unit/test_agent_event_stream.py tests/graybox/unit/test_device_log_files.py tests/graybox/unit/test_device_log_bus.py -q` 通过。
- [x] 7.2 对改动过的 Python 文件做静态检查。验证：`python -m ruff check utils/logs.py engines/agents/event_log.py engines/agents/role engines/agents/tools/tool_device.py engines/agents/tools/tool_wrapper.py engines/agents/workflow/ui_auto_workflow.py engines/ai/process_log.py engines/device apps tests/graybox/unit/test_project_log.py tests/graybox/unit/test_agent_events_show.py tests/graybox/unit/test_agent_process_log.py tests/graybox/unit/test_agent_event_stream.py` 通过。

## 8. 去掉自定义行格式

- [x] 8.1 行格式改为 logging 的时间、等级、记录器名、正文。

## 9. 收成标准 logging

- [x] 9.1 记录器改为 `logging.getLogger` + `RotatingFileHandler`（10MB、3 个备份）+ 控制台 WARNING。行格式只有时间、记录器名、等级、正文。日志模块不再拼业务字段、不再按 SKU 拆文件。验证：`python -m pytest tests/graybox/unit/test_project_log.py tests/graybox/unit/test_agent_events_show.py tests/graybox/unit/test_agent_process_log.py tests/graybox/unit/test_agent_event_stream.py tests/graybox/unit/test_device_log_files.py tests/graybox/unit/test_device_log_bus.py -q` 通过。
