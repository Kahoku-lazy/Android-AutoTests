## Why

运行日志分散在 Django 的 `logs/django.log`、loguru 的 `logs/agent_events.log`、按天切分的角色过程日志，以及各处自行挂上的 `FileHandler`。排障时要对多份文件、多套格式，也无法按后端、智能体、串口、设备四组对照同一次执行。

## What Changes

- 将包 `algorithms` 改名为 `utils`，原有 XPath、层级解析、元素分层、OCR 的导入路径一并改到 `utils`。
- 在 `utils/logs.py` 直接实例化一个全局日志对象。需要记日志的运行期类在 `__init__` 里把它赋给 `self.log`。该对象提供总开关，关闭后四组文件都不再写入。
- 四组文件、按调用顺序追加：
  - 后端代码：`logs/backend.log`
  - `engines/agents` 代码与事件时间线：`logs/agents/agent_events.log`
  - 串口相关代码：`logs/serial_logs/{SKU}_{端口}.log`
  - `engines/device` 代码：`logs/device.log`
- 每行包含时间、代码文件、类名、日志等级。涉及模型时再带角色、模型与动作。串口行再带地址、设备与串口号。
- **BREAKING**：`logs/agent_events.log` 停用，事件时间线改写到 `logs/agents/agent_events.log`，不再使用 loguru 自建通道。
- **BREAKING**：角色过程日志不再按天写 `agents-YYYYMMDD.log`，过程记录改经同一实例写入 `logs/agents/agent_events.log`。
- **BREAKING**：后端不再另写 `logs/django.log` 以及各模块自建的代码日志文件（含 `AI-MODEL-TEST.log`）。控制台输出保留。
- **BREAKING**：`android_device.py` 里 `AndroidConnection` 现有的 `self.log` 是连接过程回调，改用其它属性名，把 `self.log` 让给统一日志实例。
- 设备采集原文归档保持不变：仍落在可配置的 `logs/{SKU}_{端口}.log`，行格式仍是「北京时间 [来源] 原文」。`logs/serial_logs/` 只收串口相关代码自己的运行日志。
- 迁移文件、测试、技能脚本不挂 `self.log`。

## 关联文档

无关联需求编号。本次只调整运行日志的落盘位置与格式，不改产品功能入口。

## Capabilities

### New Capabilities

- `project-log`: 全局日志实例、四组落盘路径、行字段、总开关，以及运行期类通过 `self.log` 写入。

### Modified Capabilities

- `ai-agent-process-log`: 过程记录不再按天切到独立的 `agents-YYYYMMDD.log`，改为经全局日志实例写入 `logs/agents/agent_events.log`。思考、工具调用、工具返回仍在产生时追加，并保留角色、模型、任务与步骤。

## Impact

- 代码：`algorithms/` 整包改名；`utils/logs.py` 新增；`config/settings.py` 的文件 handler；`engines/agents/event_log.py` 与其调用方；`engines/ai/process_log.py`；`engines/device` 中会打日志的类（含 `AndroidDevice` 回调改名）；`apps/` 中现有 `logging.getLogger` 的运行期类；串口相关模块按 SKU 与端口选择文件。
- 测试：`tests/graybox/unit/test_logging_config.py`、`test_agent_process_log.py`、`test_agent_events_show.py`，以及引用 `algorithms` 的测试与 `apps/device_inspector`。
- 未归档变更 `agent-events-show-logger` 把事件写到 `logs/agent_events.log` 并用 loguru。本变更改落点与写入方式，事件的九个动作语义不变。
- 不改 `device-log-file-archive`：采集原文的目录、文件名与行格式保持原契约。
- 不改 `run.py` 对进程标准输出的捕获，也不改边界检查工具自己的 `boundary-check.log`。
